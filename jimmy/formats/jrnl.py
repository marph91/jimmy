"""Convert jrnl notes to the intermediate format."""

import datetime as dt
from pathlib import Path
import json

from jimmy import common, converter, intermediate_format as imf


class Converter(converter.BaseConverter):
    accepted_extensions = [".json"]

    @common.catch_all_exceptions
    def convert_note(self, note_jrnl):
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

    def convert(self, file_or_folder: Path):
        input_json = json.loads(file_or_folder.read_text(encoding="utf-8"))
        if "entries" not in input_json:
            self.logger.error('"entries" not found. Is this really a jrnl export?')
            return
        for note_jrnl in input_json.get("entries", []):
            self.convert_note(note_jrnl)
