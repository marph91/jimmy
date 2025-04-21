"""Convert simplenote notes to the intermediate format."""

import datetime as dt
import json
from pathlib import Path

from jimmy import common, converter, intermediate_format as imf
import jimmy.md_lib.common


class Converter(converter.BaseConverter):
    accepted_extensions = [".zip"]

    @common.catch_all_exceptions
    def convert_note(self, note_simplenote):
        # title is the first line
        title, body = jimmy.md_lib.common.split_title_from_body(
            note_simplenote["content"], h1=False
        )
        self.logger.debug(f'Converting note "{title}"')

        note_links = []
        for link in jimmy.md_lib.common.get_markdown_links(body):
            if link.is_web_link or link.is_mail_link:
                continue  # keep the original links
            if link.url.startswith("simplenote://"):
                # internal link
                _, linked_note_id = link.url.rsplit("/", 1)
                note_links.append(imf.NoteLink(str(link), linked_note_id, link.text))

        tags = note_simplenote.get("tags", [])
        if note_simplenote.get("pinned"):
            tags.append("simplenote-pinned")

        note_imf = imf.Note(
            title.strip(),
            body.lstrip(),
            created=dt.datetime.fromisoformat(note_simplenote["creationDate"]),
            updated=dt.datetime.fromisoformat(note_simplenote["lastModified"]),
            source_application=self.format,
            # Tags don't have a separate id. Just use the name as id.
            tags=[imf.Tag(tag) for tag in tags],
            note_links=note_links,
            original_id=note_simplenote["id"],
        )
        self.root_notebook.child_notes.append(note_imf)

    def convert(self, file_or_folder: Path):
        input_json = json.loads(
            (self.root_path / "source/notes.json").read_text(encoding="utf-8")
        )
        if "activeNotes" not in input_json:
            self.logger.error(
                '"activeNotes" not found. Is this really a Simplenote export?'
            )
            return

        for note_simplenote in input_json["activeNotes"]:
            self.convert_note(note_simplenote)
