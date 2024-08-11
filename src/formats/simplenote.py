"""Convert simplenote notes to the intermediate format."""

import json
from pathlib import Path

import common
import converter
import intermediate_format as imf


class Converter(converter.BaseConverter):
    accepted_extensions = [".zip"]

    def prepare_input(self, input_: Path) -> Path:
        return common.extract_zip(input_, "source/notes.json")

    def convert(self, file_or_folder: Path):
        self.root_path = self.prepare_input(file_or_folder)
        input_json = json.loads(
            (self.root_path / "source/notes.json").read_text(encoding="utf-8")
        )

        for note_simplenote in input_json["activeNotes"]:
            # title is the first line. In case of title-only notes, create empty second line
            title, body = common.split_h1_title_from_body(note_simplenote["content"])

            note_links = []
            for link in common.get_markdown_links(body):
                if link.is_web_link or link.is_mail_link:
                    continue  # keep the original links
                if link.url.startswith("simplenote://"):
                    # internal link
                    _, linked_note_id = link.url.rsplit("/", 1)
                    note_links.append(
                        imf.NoteLink(str(link), linked_note_id, link.text)
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
                    "source_application": self.format,
                },
                # Tags don't have a separate id. Just use the name as id.
                tags=[
                    imf.Tag({"title": tag}) for tag in note_simplenote.get("tags", [])
                ],
                note_links=note_links,
                original_id=note_simplenote["id"],
            )
            self.root_notebook.child_notes.append(note_joplin)
