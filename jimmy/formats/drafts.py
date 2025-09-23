"""Convert Drafts drafts to the intermediate format."""

import json
from pathlib import Path
import re

from jimmy import common, converter, intermediate_format as imf
import jimmy.md_lib.common


DRAFTS_LINK_RE = re.compile(
    r"(drafts:\/\/open\?uuid="
    r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}))"
)


class Converter(converter.BaseConverter):
    accepted_extensions = [".draftsexport"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.note_id_title_map = {}

    def handle_drafts_links(self, note_body: str) -> imf.NoteLinks:
        """
        Drafts links are raw text. Not wrapped in Markdown syntax.
        https://docs.getdrafts.com/docs/drafts/cross-linking#draft-links-urls
        """
        note_links = []
        for original_text, id_ in DRAFTS_LINK_RE.findall(note_body):
            note_links.append(imf.NoteLink(original_text, id_, ""))
        return note_links

    def handle_wikilink_links(self, body: str) -> imf.NoteLinks:
        # https://docs.getdrafts.com/docs/drafts/cross-linking#wiki-style-cross-linking-drafts
        note_links = []
        for _, url, _ in jimmy.md_lib.common.get_wikilink_links(body):
            original_text = f"[[{url}]]"
            if url.startswith("d:"):
                best_match_id = common.get_best_match(url[2:], self.note_id_title_map)
                if best_match_id is not None:
                    note_links.append(imf.NoteLink(original_text, best_match_id, ""))
            elif url.startswith("u:"):  # id
                note_links.append(imf.NoteLink(original_text, url[2:], ""))
            elif url.startswith("w:") or url.startswith("s:"):
                pass  # TODO: How to handle workspaces and search?
            else:  # no prefix
                best_match_id = common.get_best_match(url, self.note_id_title_map)
                if best_match_id is not None:
                    note_links.append(imf.NoteLink(original_text, best_match_id, ""))
        return note_links

    @staticmethod
    def get_title(content: str) -> str:
        # There is no title in drafts.
        # Simply take the first 80 characters of the first line.
        if content.strip():
            for line in content.split("\n"):
                if line.strip():
                    return line[:80].strip()
        return common.unique_title()

    @common.catch_all_exceptions
    def convert_note(self, draft):
        title = self.get_title(draft["content"])
        self.logger.debug(f'Converting draft "{title}"')

        if draft["languageGrammar"] not in ("Markdown", "Plain Text"):
            self.logger.warning(
                f'"languageGrammar={draft["languageGrammar"]}" not supported. '
                "Handling it as plain text."
            )

        note_imf = imf.Note(
            title,
            body=draft["content"],
            created=common.iso_to_datetime(draft["created_at"]),
            updated=common.iso_to_datetime(draft["modified_at"]),
            tags=[imf.Tag(title) for title in draft.get("tags", [])],
            source_application=self.format,
            original_id=draft["uuid"],
        )

        wikilink_note_links = self.handle_wikilink_links(note_imf.body)
        draft_note_links = self.handle_drafts_links(note_imf.body)
        note_imf.note_links = wikilink_note_links + draft_note_links

        if draft.get("flagged", False):
            note_imf.tags.append(imf.Tag("drafts-flagged"))

        if (longitude := draft.get("created_longitude", 0)) != 0:
            note_imf.longitude = longitude
        if (latitude := draft.get("created_latitude", 0)) != 0:
            note_imf.latitude = latitude

        self.root_notebook.child_notes.append(note_imf)

    def convert(self, file_or_folder: Path):
        input_json = json.loads(file_or_folder.read_text(encoding="utf-8"))

        # first pass: for internal links, we need to store the note titles and IDs
        for draft in input_json:
            self.note_id_title_map[draft["uuid"]] = self.get_title(draft["content"])

        # second pass: convert the notes
        for draft in input_json:
            self.convert_note(draft)
