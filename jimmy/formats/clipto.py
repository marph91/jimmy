"""Convert clipto notes to the intermediate format."""

from pathlib import Path
import json

from jimmy import common, converter, intermediate_format as imf
import jimmy.md_lib.text


class Converter(converter.BaseConverter):
    @common.catch_all_exceptions
    def convert_note(self, note_clipto: dict, tags: imf.Tags):
        text = note_clipto.get("text", "")
        if (title := note_clipto.get("title")) is None:
            title, text = jimmy.md_lib.text.split_title_from_body(text, h1=False)

        self.logger.debug(f'Converting note "{title}"')

        note_imf = imf.Note(
            title,
            text,
            created=common.iso_to_datetime(note_clipto["created"]),
            updated=common.iso_to_datetime(note_clipto["updated"]),
            source_application=self.format,
            tags=[tag for tag in tags if tag.reference_id in note_clipto.get("tagIds", [])],
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
            tags.append(imf.Tag(filter_.get("name", ""), filter_.get("uid")))

        for note_clipto in input_json.get("notes", []):
            self.convert_note(note_clipto, tags)
