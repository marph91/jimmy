"""Convert OneNote notes to the intermediate format."""

from pathlib import Path
import shutil
import subprocess
from urllib.parse import parse_qs, unquote, urlparse

from bs4 import BeautifulSoup

from jimmy import common, converter, intermediate_format as imf
import jimmy.md_lib.convert
import jimmy.md_lib.links


class Converter(converter.BaseConverter):
    def __init__(self, config: common.Config):
        super().__init__(config)
        self._input_note_index = 0
        self.temp_folder = common.get_temp_folder()

    def handle_markdown_links(
        self, body: str, note_path: Path
    ) -> tuple[imf.Resources, imf.NoteLinks]:
        note_links = []
        resources = []
        for link in jimmy.md_lib.links.get_markdown_links(body):
            link_url = unquote(link.url)
            if link_url.startswith("https://onedrive.live.com/"):
                # internal link
                wd_string = parse_qs(urlparse(link.url).query)["wd"][0]
                wd_string_splitted = wd_string[len("target(") :].split("|")
                section = wd_string_splitted[0][: -len(".one")]
                page = wd_string_splitted[1].split("/", maxsplit=1)[-1]
                note_links.append(imf.NoteLink(str(link), f"{section}/{page}", link.text))
            elif link.is_web_link or link.is_mail_link:
                continue  # keep the original links
            elif link_url.startswith("onenote:"):
                section = Path(urlparse(link_url).path).stem
                page = urlparse(link_url).fragment.split("&")[0]
                note_links.append(imf.NoteLink(str(link), f"{section}/{page}", link.text))
            elif (file_path := note_path.parent / link_url).is_file():
                if file_path.suffix != ".html":
                    # resource
                    resources.append(imf.Resource(file_path, str(link), link.text))
                else:
                    # internal link
                    note_links.append(
                        imf.NoteLink(str(link), f"{note_path.stem}/{file_path.stem}", link.text)
                    )
        return resources, note_links

    def extract_metadata(self, soup):
        # metadata is located in the first div
        if (metadata_div := soup.find("div")) is None:
            return  # TOCs don't contain the metadata
        # TODO: extract the two tags and the creation date
        metadata_div.decompose()

    def convert_note(self, page: Path, parent: imf.Notebook):
        # note == page
        body = page.read_text(encoding="utf-8")

        # get best title
        soup = BeautifulSoup(body, "html.parser")
        if (title_element := soup.find("title")) is not None and title_element.text:
            title = title_element.text
        else:
            title = page.stem

        note_imf = imf.Note(title, original_id=f"{page.parent.stem}/{title}")  # TODO: match by UUID
        self.logger.debug(f'Converting note "{title}"')

        self.extract_metadata(soup)

        # TODO: Strip title and extract date. This could be done in one2html already.
        note_imf.body = jimmy.md_lib.convert.markup_to_markdown(str(soup), pwd=page.parent)

        note_imf.resources, note_imf.note_links = self.handle_markdown_links(note_imf.body, page)

        parent.child_notes.append(note_imf)

    def convert_section_to_markdown(self, file_or_folder: Path, notebook: imf.Notebook):
        # section including TOC
        for item in sorted(file_or_folder.iterdir()):
            if item.is_file():
                # onetoc2
                if item.suffix != ".html":
                    self.logger.debug(f'Ignoring unexpected file: "{item.name}".')
                    continue
                self.convert_note(item, notebook)
            else:
                # section
                self.logger.debug(f'Converting section: "{item.stem}"')
                section = imf.Notebook(item.stem)
                notebook.child_notebooks.append(section)
                for sub_item in sorted(item.iterdir()):
                    if sub_item.is_dir():
                        # It seems that sections (folders) can't be nested.
                        self.logger.debug(f'Ignoring unexpected folder: "{sub_item.name}".')
                        continue
                    if sub_item.suffix != ".html":
                        self.logger.debug(f'Ignoring unexpected file: "{sub_item.name}".')
                        continue
                    self.convert_note(sub_item, section)

    @common.catch_all_exceptions
    def convert_section_and_toc(self, file_or_folder: Path, parent: imf.Notebook):
        """
        Convert onenote sections (.one) and the TOC (.onetoc2) to HTML files in a folder hierarchy.
        Folders represent OneNote sections and files represent OneNote pages.
        """
        intermediate_html_folder = self.temp_folder / str(self._input_note_index)
        intermediate_html_folder.mkdir()
        self._input_note_index += 1

        # onenote -> HTML
        # fmt: off
        proc = subprocess.run(
            [
                "one2html",
                "--input", str(file_or_folder.resolve()),
                "--output", str(intermediate_html_folder.resolve()),
            ],
            capture_output=True,
            check=False,  # check is done manually afterwards
            encoding="utf8",
        )
        # fmt: on
        if proc.returncode != 0:
            self.logger.warning(f"one2html error code: {proc.returncode}")
            self.logger.debug(proc.stderr.strip())
            return

        # HTML -> Markdown
        self.convert_section_to_markdown(intermediate_html_folder, parent)

    def convert_notebook(self, root_path: Path):
        # Only single notebooks can be exported.
        notebook_path = common.get_single_child_folder(root_path)

        root_notebook = imf.Notebook(notebook_path.stem)
        self.logger.debug(f'Converting notebook: "{root_notebook.title}"')
        self.root_notebook.child_notebooks.append(root_notebook)
        for item in sorted(notebook_path.iterdir()):
            if item.name == ".onetoc2":
                # The root TOC seems to be named ".onetoc2".
                # The external OneNote converter can't handle this.
                new_path = item.parent / (root_notebook.title + ".onetoc2")
                item.rename(new_path)
                item = new_path
                continue  # TODO: still doesn't get converted
            if item.suffix not in (".one", ".onetoc2"):
                self.logger.debug(f'Ignoring unexpected file: "{item.name}".')
                continue
            self.convert_section_and_toc(item, root_notebook)

    def convert_file_or_folder(self, file_or_folder: Path):
        if file_or_folder.is_file():
            self.convert_notebook(self.root_path)
        else:
            for onenote_zip in file_or_folder.glob("*.zip"):
                root_path = common.extract_zip(onenote_zip)
                self.convert_notebook(root_path)

    def convert(self, file_or_folder: Path):
        # notebook > section > page
        shutil_path = shutil.which("one2html")
        if shutil_path is None:
            self.logger.error('"one2html" binary not found.')
            return
        self.logger.debug(f"Using one2html from: {shutil_path}")
        self.logger.debug(f'temp_folder: "{self.temp_folder}"')
        self.convert_file_or_folder(file_or_folder)
