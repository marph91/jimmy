"""Convert simplenote notes to the intermediate format."""

import json
from pathlib import Path

from jimmy import common, converter, intermediate_format as imf
import jimmy.md_lib.common


def extract_tags_from_body(body: str) -> tuple[str, list[str]]:
    r"""
    >>> extract_tags_from_body("body\r\n\r\n\r\nTags:\r\n  Ed, NxtProject, Reference")
    ('body\n\n', ['Ed', 'NxtProject', 'Reference'])
    >>> extract_tags_from_body("body, no tags")
    ('body, no tags', [])
    """
    body_lines = body.splitlines()
    if len(body_lines) > 1 and body_lines[-2] == "Tags:":
        return "\n".join(body_lines[:-2]), body_lines[-1].strip().split(", ")
    return body, []


class Converter(converter.BaseConverter):
    accepted_extensions = [".zip"]

    @common.catch_all_exceptions
    def convert_note(self, note_simplenote):
        # title is the first line
        title, body = jimmy.md_lib.common.split_title_from_body(
            note_simplenote["content"], h1=False
        )
        self.logger.debug(f'Converting note "{title}"')

        note_imf = imf.Note(
            title.strip(),
            created=common.iso_to_datetime(note_simplenote["creationDate"]),
            updated=common.iso_to_datetime(note_simplenote["lastModified"]),
            source_application=self.format,
            original_id=note_simplenote["id"],
        )

        for link in jimmy.md_lib.common.get_markdown_links(body):
            if link.is_web_link or link.is_mail_link:
                continue  # keep the original links
            if link.url.startswith("simplenote://"):
                # internal link
                _, linked_note_id = link.url.rsplit("/", 1)
                note_imf.note_links.append(
                    imf.NoteLink(str(link), linked_note_id, link.text)
                )

        note_imf.tags = [imf.Tag(tag) for tag in note_simplenote.get("tags", [])]
        if note_simplenote.get("pinned"):
            note_imf.tags.append(imf.Tag("simplenote-pinned"))
        # sometimes tags are appended like "Tags:\n  Tag1, Tag2"
        body_without_tags, body_tags = extract_tags_from_body(body)
        note_imf.tags.extend([imf.Tag(tag) for tag in body_tags])

        note_imf.body = body_without_tags.lstrip()

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
