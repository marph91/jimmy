"""Convert jrnl notes to the intermediate format."""

from pathlib import Path
import json

from common import iso_to_unix_ms
import converter
import intermediate_format as imf


class Converter(converter.BaseConverter):
    accepted_extensions = [".json"]

    def convert(self, file_or_folder: Path):
        file_dict = json.loads(file_or_folder.read_text(encoding="utf-8"))
        for note_jrnl in file_dict.get("entries", []):
            title = f"{note_jrnl['date']} {note_jrnl['time']} {note_jrnl['title']}"
            unix_time = iso_to_unix_ms(f"{note_jrnl['date']}T{note_jrnl['time']}")

            tags = [tag.lstrip("@") for tag in note_jrnl["tags"]]
            if note_jrnl["starred"]:
                tags.append("jrnl-starred")

            note_joplin = imf.Note(
                {
                    "title": title,
                    "body": note_jrnl["body"],
                    "user_created_time": unix_time,
                    "user_updated_time": unix_time,
                    "source_application": self.format,
                },
                tags=[imf.Tag({"title": tag}) for tag in tags],
            )
            self.root_notebook.child_notes.append(note_joplin)
