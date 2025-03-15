"""Convert clipto notes to the intermediate format."""

import datetime as dt
from pathlib import Path
import json

import common
import converter
import intermediate_format as imf


class Converter(converter.BaseConverter):
    accepted_extensions = [".json"]

    @common.catch_all_exceptions
    def convert_note(self, note_clipto: dict, tags: imf.Tags):
        title = note_clipto["title"]
        self.logger.debug(f'Converting note "{title}"')
        note_imf = imf.Note(
            title,
            note_clipto["text"],
            created=dt.datetime.fromisoformat(note_clipto["created"]),
            updated=dt.datetime.fromisoformat(note_clipto["updated"]),
            source_application=self.format,
            tags=[tag for tag in tags if tag.reference_id in note_clipto["tagIds"]],
        )
        self.root_notebook.child_notes.append(note_imf)

    def convert(self, file_or_folder: Path):
        input_json = json.loads(file_or_folder.read_text(encoding="utf-8"))
        if "notes" not in input_json:
            self.logger.error('"notes" not found. Is this really a clipto export?')
            return

        tags = []
        # tags are contained in filters
        for filter_ in input_json.get("filters"):
            tags.append(imf.Tag(filter_["name"], filter_["uid"]))

        for note_clipto in input_json.get("notes", []):
            self.convert_note(note_clipto, tags)
