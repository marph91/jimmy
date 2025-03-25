"""Convert Drafts drafts to the intermediate format."""

import datetime as dt
import json
from pathlib import Path

import common
import converter
import intermediate_format as imf


class Converter(converter.BaseConverter):
    accepted_extensions = [".draftsexport"]

    @common.catch_all_exceptions
    def convert_note(self, draft):
        title = dt.datetime.fromisoformat(draft["created_at"]).strftime(
            "%Y-%m-%d %H:%M"
        )
        self.logger.debug(f'Converting draft "{title}"')

        if draft["languageGrammar"] not in ("Markdown", "Plain Text"):
            self.logger.warning(
                f'"languageGrammar={draft["languageGrammar"]}" not supported. '
                "Handling it as plain text."
            )

        note_imf = imf.Note(
            title,
            body=draft["content"],
            created=dt.datetime.fromisoformat(draft["created_at"]),
            updated=dt.datetime.fromisoformat(draft["modified_at"]),
            tags=[imf.Tag(title) for title in draft.get("tags", [])],
            source_application=self.format,
            original_id=draft["uuid"],
        )

        if draft.get("flagged", False):
            note_imf.tags.append(imf.Tag("drafts-flagged"))

        if (longitude := draft.get("created_longitude", 0)) != 0:
            note_imf.longitude = longitude
        if (latitude := draft.get("created_latitude", 0)) != 0:
            note_imf.latitude = latitude

        self.root_notebook.child_notes.append(note_imf)

    def convert(self, file_or_folder: Path):
        input_json = json.loads(file_or_folder.read_text(encoding="utf-8"))

        for draft in input_json:
            self.convert_note(draft)
