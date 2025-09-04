"""Convert nimbus notes to the intermediate format."""

from pathlib import Path
from urllib.parse import unquote

from bs4 import BeautifulSoup

from jimmy import common, converter, intermediate_format as imf
import jimmy.md_lib.common
import jimmy.md_lib.html_filter


class Converter(converter.BaseConverter):
    accepted_extensions = [".zip"]
    accept_folder = True

    def __init__(self, config):
        super().__init__(config)
        self.temp_folder = common.get_temp_folder()

    def handle_markdown_links(
        self, note_body: str, root_folder: Path
    ) -> tuple[imf.Resources, imf.NoteLinks]:
        note_links = []
        resources = []
        for link in jimmy.md_lib.common.get_markdown_links(note_body):
            if link.is_web_link or link.is_mail_link:
                continue  # keep the original links
            if "nimbusweb.me" in link.url:
                # internal link
                # TODO: Get export file with internal links.
                self.logger.debug(
                    f"Skip internal link {link.url}, because there is no test data."
                )
            elif link.url.startswith("nimbusnote://"):
                linked_note_name = unquote(link.url[len("nimbusnote://") :])
                note_links.append(
                    imf.NoteLink(
                        str(link), linked_note_name, link.text or linked_note_name
                    )
                )
            elif (root_folder / link.url).is_file():
                # resource
                resources.append(
                    imf.Resource(root_folder / link.url, str(link), link.text)
                )
            elif link.url.startswith("data:image/svg+xml;base64,"):
                # TODO: Generalize for other mime types.
                # For example "data:image/png;base64,"
                base64_data = link.url[len("data:image/svg+xml;base64,") :]
                original_name = link.text
                temp_filename = root_folder / (original_name or common.unique_title())
                temp_filename = common.write_base64(temp_filename, base64_data)
                resources.append(
                    imf.Resource(
                        temp_filename,
                        f"{'!' * link.is_image}[{link.text}]({link.url})",
                        temp_filename.name,
                    )
                )
        return resources, note_links

    @common.catch_all_exceptions
    def convert_note(self, file_: Path, parent: imf.Notebook):
        self.logger.debug(f'Converting note "{file_.stem}"')
        temp_folder_note = self.temp_folder / file_.stem
        temp_folder_note.mkdir()
        common.extract_zip(file_, temp_folder=temp_folder_note)

        if not (temp_folder_note / "note.html").is_file():
            self.logger.error(
                "Export structure not implemented yet. Please report at Github."
            )
            return

        # HTML note seems to have the name "note.html" always
        note_html = (temp_folder_note / "note.html").read_text(encoding="utf-8")

        # Use the filename only as fallback title,
        # because some characters might be replaced.
        # TODO: soup is created for filtering again
        soup = BeautifulSoup(note_html, "html.parser")
        if (title_element := soup.find("title")) is not None and title_element.text:
            title = title_element.text
        else:
            title = file_.stem

        note_body_markdown = jimmy.md_lib.common.markup_to_markdown(
            note_html,
            custom_filter=[
                jimmy.md_lib.html_filter.nimbus_note_add_mark,
                jimmy.md_lib.html_filter.nimbus_note_add_note_links,
                jimmy.md_lib.html_filter.nimbus_note_streamline_lists,
                jimmy.md_lib.html_filter.nimbus_note_streamline_tables,
            ],
        )
        resources, note_links = self.handle_markdown_links(
            note_body_markdown, temp_folder_note
        )
        note_imf = imf.Note(
            title,
            note_body_markdown.strip(),
            source_application=self.format,
            resources=resources,
            note_links=note_links,
            original_id=title,
        )
        parent.child_notes.append(note_imf)

    def convert_folder(self, file_or_folder: Path, parent: imf.Notebook):
        for item in sorted(file_or_folder.iterdir()):
            if item.is_dir():
                new_parent = imf.Notebook(item.name)
                self.convert_folder(item, new_parent)
                parent.child_notebooks.append(new_parent)
            elif item.suffix == ".zip":
                self.convert_note(item, parent)

    def convert(self, file_or_folder: Path):
        if file_or_folder.suffix == ".zip":
            self.convert_note(file_or_folder, self.root_notebook)
        else:  # folder of .zip
            self.convert_folder(file_or_folder, self.root_notebook)

        # Don't export empty notebooks
        self.remove_empty_notebooks()
