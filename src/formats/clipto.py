"""Convert clipto notes to the intermediate format."""

import datetime as dt
from pathlib import Path
import json

import converter
import intermediate_format as imf


class Converter(converter.BaseConverter):
    accepted_extensions = [".json"]

    def convert(self, file_or_folder: Path):
        file_dict = json.loads(file_or_folder.read_text(encoding="utf-8"))
        tags = []
        # tags are contained in filters
        for filter_ in file_dict.get("filters"):
            tags.append(imf.Tag(filter_["name"], filter_["uid"]))

        for note_clipto in file_dict.get("notes", []):
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
