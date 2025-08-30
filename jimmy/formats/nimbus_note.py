"""Convert nimbus notes to the intermediate format."""

from pathlib import Path
from urllib.parse import unquote

from jimmy import common, converter, intermediate_format as imf
import jimmy.md_lib.common
import jimmy.md_lib.html_filter


class Converter(converter.BaseConverter):
    accepted_extensions = [".zip"]
    accept_folder = True

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
                linked_note_name = unquote(Path(link.url).stem)
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
    def convert_note(self, file_: Path, temp_folder: Path):
        title = file_.stem
        self.logger.debug(f'Converting note "{title}"')
        temp_folder_note = temp_folder / file_.stem
        temp_folder_note.mkdir()
        common.extract_zip(file_, temp_folder=temp_folder_note)

        if not (temp_folder_note / "note.html").is_file():
            self.logger.error(
                "Export structure not implemented yet. Please report at Github."
            )
            return

        # HTML note seems to have the name "note.html" always
        note_body_html = (temp_folder_note / "note.html").read_text(encoding="utf-8")
        note_body_markdown = jimmy.md_lib.common.markup_to_markdown(
            note_body_html,
            custom_filter=[
                jimmy.md_lib.html_filter.nimbus_note_add_mark,
                jimmy.md_lib.html_filter.nimbus_note_add_note_links,
                jimmy.md_lib.html_filter.nimbus_note_streamline_lists,
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
        self.root_notebook.child_notes.append(note_imf)

    def convert(self, file_or_folder: Path):
        temp_folder = common.get_temp_folder()

        if file_or_folder.suffix == ".zip":
            self.convert_note(file_or_folder, temp_folder)
        else:  # folder of .zip
            for file_ in sorted(file_or_folder.rglob("*.zip")):
                self.convert_note(file_, temp_folder)
