"""Convert clipto notes to the intermediate format."""

from pathlib import Path
import json

from common import iso_to_unix_ms
import converter
import intermediate_format as imf


class Converter(converter.BaseConverter):
    def convert(self, file_or_folder: Path):
        # export only possible in android app:
        # - https://github.com/clipto-pro/Desktop/issues/21#issuecomment-537401330
        # - settings -> time machine -> backup to file

        file_dict = json.loads(file_or_folder.read_text(encoding="UTF-8"))
        tags = []
        # tags are contained in filters
        for filter_ in file_dict.get("filters"):
            tags.append(imf.Tag({"title": filter_["name"]}, filter_["uid"]))

        for note_clipto in file_dict.get("notes", []):
            note_joplin = imf.Note(
                {
                    "title": note_clipto["title"],
                    "body": note_clipto["text"],
                    "user_created_time": iso_to_unix_ms(note_clipto["created"]),
                    "user_updated_time": iso_to_unix_ms(note_clipto["updated"]),
                    "source_application": self.app,
                },
                tags=[tag for tag in tags if tag.original_id in note_clipto["tagIds"]],
            )
            self.root_notebook.child_notes.append(note_joplin)
