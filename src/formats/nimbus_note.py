"""Convert nimbus notes to the intermediate format."""

import base64
from pathlib import Path

from bs4 import BeautifulSoup

import common
import converter
import intermediate_format as imf
import markdown_lib.common


def clean_tables(soup):
    for table in soup.find_all("table"):
        tags_to_remove = ["div", "span"]
        for tag in tags_to_remove:
            for element in table.find_all(tag):
                element.unwrap()


def assign_lists(_soup):
    # TODO:
    # - all lists are unnumbered lists (ul)
    #   - type is in the class attr (list-item-number, -bullet, -checkbox)
    # - indentation is in the class attr (indent-0)

    # for task_list in soup.find_all("ul", class_="checklist"):
    #     ...
    pass


class Converter(converter.BaseConverter):
    accept_folder = True

    def handle_markdown_links(self, note_body: str, root_folder: Path) -> imf.Resources:
        resources = []
        for link in markdown_lib.common.get_markdown_links(note_body):
            if link.is_web_link or link.is_mail_link:
                continue  # keep the original links
            if "nimbusweb.me" in link.url:
                # internal link
                # TODO: Get export file with internal links.
                self.logger.debug(
                    f"Skip internal link {link.url}, because there is no test data."
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
                temp_filename.write_bytes(base64.b64decode(base64_data))
                resources.append(
                    imf.Resource(
                        temp_filename,
                        f"{'!' * link.is_image}[{link.text}]({link.url})",
                        temp_filename.name,
                    )
                )
        return resources

    def convert(self, file_or_folder: Path):
        temp_folder = common.get_temp_folder()

        for file_ in sorted(file_or_folder.rglob("*.zip")):
            title = file_.stem
            self.logger.debug(f'Converting note "{title}"')
            temp_folder_note = temp_folder / file_.stem
            temp_folder_note.mkdir()
            common.extract_zip(file_, temp_folder=temp_folder_note)

            # HTML note seems to have the name "note.html" always
            note_body_html = (temp_folder_note / "note.html").read_text(
                encoding="utf-8"
            )

            soup = BeautifulSoup(note_body_html, "html.parser")
            clean_tables(soup)
            assign_lists(soup)

            note_body_markdown = markdown_lib.common.markup_to_markdown(str(soup))
            resources = self.handle_markdown_links(note_body_markdown, temp_folder_note)
            note_imf = imf.Note(
                title,
                note_body_markdown.strip(),
                source_application=self.format,
                resources=resources,
            )
            self.root_notebook.child_notes.append(note_imf)
