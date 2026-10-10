"""Convert notion notes to the intermediate format."""

import io
from pathlib import Path
import re
import shutil
from urllib.parse import unquote
import zipfile

from jimmy import common, converter, intermediate_format as imf
import jimmy.md_lib.convert
import jimmy.md_lib.links
import jimmy.md_lib.text


def get_title_from_filename(filename: str) -> str:
    """
    >>> get_title_from_filename("page with link c2c6b297ba154afba1c846761760aa78")
    'page with link'

    # this shouldn't happen in practice
    # just make sure there is no exception
    >>> get_title_from_filename("no ID")
    'no'
    >>> get_title_from_filename("noid")
    'noid'
    """
    if " " in filename:
        # id is appended to filename
        title, _id = filename.rsplit(" ", 1)
        return title
    # no ID - only title
    return filename


def get_id_from_filename(filename: str) -> str | None:
    """
    >>> get_id_from_filename("page with link c2c6b297ba154afba1c846761760aa78")
    'c2c6b297ba154afba1c846761760aa78'

    # this shouldn't happen in practice
    # just make sure there is no exception
    >>> get_id_from_filename("no ID")
    'ID'
    >>> get_id_from_filename("noid")
    """
    if " " in filename:
        # id is appended to filename
        _filename, id_ = filename.rsplit(" ", 1)
        return id_
    # no ID - only title
    return None


class Converter(converter.BaseConverter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id_path_map: dict[str | None, Path] = {".": Path(".")}

    def prepare_input(self, input_: Path) -> Path:
        temp_folder = common.get_temp_folder()

        # unzip nested zip file in notion format
        with zipfile.ZipFile(input_) as zip_ref:
            is_zip = [f.endswith(".zip") for f in zip_ref.namelist()]
            if all(is_zip):
                # usual structure: zip of zips
                for nested_zip_name in zip_ref.namelist():
                    with zip_ref.open(nested_zip_name) as nested_zip:
                        nested_zip_filedata = io.BytesIO(nested_zip.read())
                        with zipfile.ZipFile(nested_zip_filedata) as nested_zip_ref:
                            nested_zip_ref.extractall(temp_folder)
                temp_folder = common.get_single_child_folder(temp_folder)
            elif not any(is_zip):
                # unusual structure: zipped files
                # guess that the user extracted the outer zip already
                zip_ref.extractall(temp_folder)
            else:
                # unusual structure: zipped files and other files
                # stop here
                self.logger.error("Unexpected file formats inside zip.")
                return temp_folder

        # remove macOS trash? folder
        shutil.rmtree(temp_folder / "__MACOSX", ignore_errors=True)

        return temp_folder

    def handle_markdown_links(self, body: str, item: Path) -> tuple[imf.Resources, imf.NoteLinks]:
        resources = []
        note_links = []
        for link in jimmy.md_lib.links.get_markdown_links(body):
            if link.is_web_link or link.is_mail_link:
                continue  # keep the original links
            unquoted_url = unquote(link.url)
            if Path(link.url).suffix in common.MARKDOWN_SUFFIXES + (".html",):
                # internal link
                linked_note_id = get_id_from_filename(Path(unquoted_url).stem)
                if linked_note_id is None:
                    self.logger.debug(f'Unhandled link "{link}" - linked ID not found')
                    continue
                note_links.append(
                    imf.NoteLink(
                        str(link),
                        linked_note_id,
                        link.text,
                        fragment=link.fragment,
                        title=link.title,
                    )
                )
            elif (item.parent / unquoted_url).is_file():
                # resource
                resources.append(imf.Resource(item.parent / unquoted_url, str(link), link.text))
            else:
                self.logger.debug(f'Unhandled link "{link}"')
        return resources, note_links

    @common.catch_all_exceptions()
    def convert_note(self, item: Path, relative_parent_path: Path, parent_notebook: imf.Notebook):
        if (
            item.is_file()
            and item.suffix.lower() not in common.MARKDOWN_SUFFIXES + (".html",)
            or item.name == "index.html"
        ):
            return

        if item.is_dir():
            # check if there is a note with same name, but with suffix:
            # yes - ID included -> extract ID from title
            # no - ID not included -> extract ID from note title
            if (
                item.with_suffix(".md").is_file()
                or item.with_suffix(".html").is_file()
                or item.with_suffix(".csv").is_file()
            ):
                title = get_title_from_filename(item.name)
                id_ = get_id_from_filename(item.name)
            else:
                # fallback values
                title = item.name
                id_ = None

                # TODO: a first pass iterating over all notes and collecting IDs could be faster
                id_from_file_regex = re.compile(f"^{item.name} ([a-z0-9]{{32}}).(?:md|html|csv)$")
                for parent_item in item.parent.iterdir():
                    if id_from_file_regex.search(parent_item.name):
                        title = get_title_from_filename(parent_item.stem)
                        id_ = get_id_from_filename(parent_item.stem)
                        break
        else:
            title = get_title_from_filename(item.stem)
            id_ = get_id_from_filename(item.stem)

        # propagate the path through all parents
        # separator is always "/"
        if id_ is None:
            self.logger.debug(f'no ID found for note "{item.name}"')
        if parent_notebook.original_id != ".":
            self.id_path_map[id_] = relative_parent_path / item.name
        else:
            self.id_path_map[id_] = Path(item.name)

        if item.is_dir():
            child_notebook = imf.Notebook(title, original_id=id_)
            self.convert_directory(child_notebook)
            # It can happen that the folder only contains resources.
            # They are added to the note one level higher with the same name.
            # In this case, the notebook is no longer of use.
            if not child_notebook.is_empty():
                parent_notebook.child_notebooks.append(child_notebook)
            return

        self.logger.debug(f'Converting note "{title}"')
        body = item.read_text(encoding="utf-8")
        if item.suffix.lower() == ".html":
            # html, else markdown
            body = jimmy.md_lib.convert.markup_to_markdown(
                body,
                pwd=item.parent,
                custom_filter=[jimmy.md_lib.html_filter.notion_streamline_lists],
            )
        _, body = jimmy.md_lib.text.split_title_from_body(body)

        # find links
        resources, note_links = self.handle_markdown_links(body, item)

        note_imf = imf.Note(
            title,
            body,
            source_application=self.format,
            original_id=id_,
            resources=resources,
            note_links=note_links,
        )
        parent_notebook.child_notes.append(note_imf)

    def convert_directory(self, parent_notebook):
        relative_parent_path = self.id_path_map[parent_notebook.original_id]

        for item in sorted((self.root_path / relative_parent_path).iterdir()):
            self.convert_note(item, relative_parent_path, parent_notebook)

    def convert(self, file_or_folder: Path):
        self.root_notebook.original_id = "."
        self.convert_directory(self.root_notebook)
