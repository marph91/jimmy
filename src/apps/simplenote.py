"""Convert simplenote notes to the intermediate format."""

import json
from pathlib import Path

import common
import converter
import intermediate_format as imf


class Converter(converter.BaseConverter):
    def prepare_input(self, input_: Path) -> Path | None:
        if input_.suffix.lower() == ".zip":
            return common.extract_zip(input_, "source/notes.json")
        self.logger.error(f"Unsupported format for {self.app}")
        return None

    def convert(self, file_or_folder: Path):
        self.root_path = self.prepare_input(file_or_folder)
        if self.root_path is None:
            return
        input_json = json.loads((self.root_path / "source/notes.json").read_text())

        for note_simplenote in input_json["activeNotes"]:
            # title is the first line
            title, body = note_simplenote["content"].split("\r\n", maxsplit=1)

            note_links = []
            for file_prefix, description, url in common.get_markdown_links(body):
                if url.startswith("http"):
                    continue  # web link
                if url.startswith("simplenote://"):
                    # internal link
                    _, linked_note_id = url.rsplit("/", 1)
                    note_links.append(
                        imf.NoteLink(
                            f"{file_prefix}[{description}]({url})",
                            linked_note_id,
                            description,
                        )
                    )
            note_joplin = imf.Note(
                {
                    "title": title.strip(),
                    "body": body.lstrip(),
                    "user_created_time": common.iso_to_unix_ms(
                        note_simplenote["creationDate"]
                    ),
                    "user_updated_time": common.iso_to_unix_ms(
                        note_simplenote["lastModified"]
                    ),
                    "source_application": self.app,
                },
                # Tags don't have a separate id. Just use the name as id.
                tags=[
                    imf.Tag({"title": tag}) for tag in note_simplenote.get("tags", [])
                ],
                note_links=note_links,
                original_id=note_simplenote["id"],
            )
            self.root_notebook.child_notes.append(note_joplin)
