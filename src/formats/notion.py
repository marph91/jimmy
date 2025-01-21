"""Convert notion notes to the intermediate format."""

import io
from pathlib import Path
import shutil
from urllib.parse import unquote
import zipfile

import common
import converter
import intermediate_format as imf
import markdown_lib.common


class Converter(converter.BaseConverter):
    accepted_extensions = [".zip"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id_path_map = {".": "."}

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

        # remove MacOS trash? folder
        shutil.rmtree(temp_folder / "__MACOSX", ignore_errors=True)

        return temp_folder

    def handle_markdown_links(
        self, body: str, item: Path
    ) -> tuple[imf.Resources, imf.NoteLinks]:
        resources = []
        note_links = []
        for link in markdown_lib.common.get_markdown_links(body):
            if link.is_web_link or link.is_mail_link:
                continue  # keep the original links
            unquoted_url = unquote(link.url)
            if link.url.endswith(".md") or link.url.endswith(".html"):
                # internal link
                _, linked_note_id = Path(unquoted_url).stem.rsplit(" ", 1)
                note_links.append(imf.NoteLink(str(link), linked_note_id, link.text))
            elif (item.parent / unquoted_url).is_file():
                # resource
                resources.append(
                    imf.Resource(item.parent / unquoted_url, str(link), link.text)
                )
            else:
                self.logger.debug(f'Unhandled link "{link}"')
        return resources, note_links

    @common.catch_all_exceptions
    def convert_note(
        self, item: Path, relative_parent_path: str, parent_notebook: imf.Notebook
    ):
        if (
            item.is_file()
            and item.suffix.lower() not in (".md", ".html")
            or item.name == "index.html"
        ):
            return
        # id is appended to filename
        title, _ = item.name.rsplit(" ", 1)

        # propagate the path through all parents
        # separator is always "/"
        _, id_ = item.stem.rsplit(" ", 1)
        if parent_notebook.original_id != ".":
            self.id_path_map[id_] = relative_parent_path + "/" + item.name
        else:
            # TODO: check if "./" works on windows
            self.id_path_map[id_] = item.name

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
        if item.suffix.lower() == ".md":
            # first line is title, second is whitespace
            body = "\n".join(item.read_text(encoding="utf-8").split("\n")[2:])
        else:  # html
            body = markdown_lib.common.markup_to_markdown(
                body, custom_filter=[markdown_lib.html_filter.notion_streamline_lists]
            )

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
