"""Convert jrnl notes to the intermediate format."""

import datetime as dt
from pathlib import Path
import json

import converter
import intermediate_format as imf


class Converter(converter.BaseConverter):
    accepted_extensions = [".json"]

    def convert(self, file_or_folder: Path):
        file_dict = json.loads(file_or_folder.read_text(encoding="utf-8"))
        for note_jrnl in file_dict.get("entries", []):
            title = f"{note_jrnl['date']} {note_jrnl['time']} {note_jrnl['title']}"
            self.logger.debug(f'Converting note "{title}"')

            unix_time = dt.datetime.fromisoformat(
                f"{note_jrnl['date']}T{note_jrnl['time']}"
            )

            tags = [tag.lstrip("@") for tag in note_jrnl["tags"]]
            if note_jrnl["starred"]:
                tags.append("jrnl-starred")

            note_imf = imf.Note(
                title,
                note_jrnl["body"],
                created=unix_time,
                updated=unix_time,
                source_application=self.format,
                tags=[imf.Tag(tag) for tag in tags],
            )
            self.root_notebook.child_notes.append(note_imf)
