"""Convert Standard Notes notes to the intermediate format."""

from collections import defaultdict
import datetime as dt
import json
from pathlib import Path

import common
import converter
import intermediate_format as imf


class Converter(converter.BaseConverter):
    accepted_extensions = [".zip"]

    def prepare_input(self, input_: Path) -> Path:
        return common.extract_zip(input_, "Standard Notes Backup and Import File.txt")

    def convert(self, file_or_folder: Path):
        self.root_path = self.prepare_input(file_or_folder)
        input_json = json.loads(
            (self.root_path / "Standard Notes Backup and Import File.txt").read_text(
                encoding="utf-8"
            )
        )

        # first pass: get all tags
        # In the export, notes are assigned to tags. We need tags assigned to notes.
        note_id_tag_map = defaultdict(list)
        for item in input_json["items"]:
            if item["content_type"] != "Tag" or item["deleted"]:
                continue
            tag = imf.Tag(
                item["content"]["title"],
                original_id=item["uuid"],
            )
            for reference in item["content"]["references"]:
                note_id_tag_map[reference["uuid"]].append(tag)

        archive_notebook = imf.Notebook("Archive")
        trash_notebook = imf.Notebook("Trash")
        self.root_notebook.child_notebooks.extend([archive_notebook, trash_notebook])

        # second pass: get all notes and assign tags to notes
        for item in input_json["items"]:
            if item["content_type"] != "Note" or item["deleted"]:
                continue
            title = item["content"]["title"]
            self.logger.debug(f'Converting note "{title}"')

            tags = note_id_tag_map.get(item["uuid"], [])
            if item["content"].get("starred", False):
                tags.append(imf.Tag("standard_notes-starred"))

            note_imf = imf.Note(
                title,
                # TODO: "noteType" is ignored for now.
                item["content"]["text"],
                created=dt.datetime.fromisoformat(item["created_at"]),
                updated=dt.datetime.fromisoformat(item["updated_at"]),
                source_application=self.format,
                # Tags don't have a separate id. Just use the name as id.
                tags=tags,
                original_id=item["uuid"],
            )
            if item["content"].get("trashed", False):
                parent = trash_notebook
            elif item["content"]["appData"]["org.standardnotes.sn"].get(
                "archived", False
            ):
                parent = archive_notebook
            else:
                parent = self.root_notebook
            parent.child_notes.append(note_imf)
