"""Convert Zoho Notebook notes to the intermediate format."""

import json
from pathlib import Path

from bs4 import BeautifulSoup

from jimmy import common, converter, intermediate_format as imf
import jimmy.md_lib.common


class Converter(converter.BaseConverter):
    def prepare_input(self, input_: Path) -> Path:
        unzipped_input = common.extract_zip(input_)
        # There is always one subfolder that contains all data.
        return common.get_single_child_folder(unzipped_input)

    def handle_markdown_links(self, note_body: str) -> tuple[imf.Resources, imf.NoteLinks]:
        resources = []
        note_links = []
        for link in jimmy.md_lib.common.get_markdown_links(note_body):
            if link.is_web_link or link.is_mail_link:
                continue  # keep the original links
            if link.url.startswith("zohonotebook://"):
                # internal link
                _, linked_note_id = link.url.rsplit("/", 1)
                note_links.append(
                    imf.NoteLink(
                        str(link),
                        linked_note_id,
                        # TODO: seems like internal links are always named "link"
                        link.text,
                    )
                )
            elif (self.root_path / link.url).is_file():
                # resource
                resources.append(imf.Resource(self.root_path / link.url, str(link), link.text))
        return resources, note_links

    @common.catch_all_exceptions
    def convert_note(self, file_: Path):
        soup = BeautifulSoup(file_.read_text(encoding="utf-8"), "html.parser")

        # parse metadata and convert it to the intermediate format
        metadata = {}
        if soup.body is not None:
            for key, value in soup.body.attrs.items():
                metadata[key] = json.loads(value)

        title = metadata["data-notecard"]["name"]
        self.logger.debug(f'Converting note "{title}" (ID: "{file_.stem}")')

        note_imf = imf.Note(
            title,
            created=common.iso_to_datetime(metadata["data-notecard"]["created_date"]),
            updated=common.iso_to_datetime(metadata["data-notecard"]["modified_date"]),
            source_application=self.format,
            tags=[imf.Tag(tag) for tag in metadata.get("data-tag", [])],
            original_id=file_.stem,
        )

        # remaining note metadata
        if (color := metadata["data-notecard"].get("color")) is not None:
            note_imf.custom_metadata["color"] = color

        for index, reminder in enumerate(metadata.get("data-remainder", [])):
            note_imf.custom_metadata[f"reminder_{index}"] = common.iso_to_datetime(
                reminder["ZReminderTime"]
            )

        # convert the note body to Markdown
        if soup.body is not None:
            note_imf.body = jimmy.md_lib.common.markup_to_markdown(str(soup), pwd=file_.parent)

            # resources and internal links
            note_imf.resources, note_imf.note_links = self.handle_markdown_links(note_imf.body)

        # get or find parent notebook
        # Assume that notebooks can't be nested.
        notebook_imf = imf.Notebook(
            metadata["data-notebook"]["name"],
            created=common.iso_to_datetime(metadata["data-notebook"]["created_date"]),
            updated=common.iso_to_datetime(metadata["data-notebook"]["modified_date"]),
        )
        parent_notebook = None
        for potential_parent in self.root_notebook.child_notebooks:
            # TODO: Is there a notebook ID? We just identify by name and creation date.
            if (
                potential_parent.title == notebook_imf.title
                and potential_parent.created == notebook_imf.created
                and potential_parent.updated == notebook_imf.updated
            ):
                # Use the existing notebook if possible.
                parent_notebook = potential_parent
                break

        # If there is no matching parent, create one.
        if parent_notebook is None:
            parent_notebook = notebook_imf
            self.root_notebook.child_notebooks.append(parent_notebook)

        parent_notebook.child_notes.append(note_imf)

    def convert(self, file_or_folder: Path):
        for item in sorted(self.root_path.iterdir()):
            if item.suffix != ".html" or item.name == "index.html":
                continue  # we want only the notes

            self.convert_note(item)
