"""Convert QOwnNotes notes to the intermediate format."""

from collections import defaultdict
from pathlib import Path
import re
import sqlite3
from urllib.parse import unquote

import common
import converter
import intermediate_format as imf


QOWNNOTE_LINK_RE = re.compile(r"<(.*?.md)>")


def get_qownnote_links(body: str) -> list[str]:
    """
    Parse QOwnNote style links.
    https://www.qownnotes.org/getting-started/markdown.html#internal-links

    >>> get_qownnote_links("no link")
    []
    >>> get_qownnote_links("<one link.md>")
    ['one link.md']
    >>> get_qownnote_links("<link 1.md> <link 2.md>")
    ['link 1.md', 'link 2.md']
    """
    return QOWNNOTE_LINK_RE.findall(body)


class Converter(converter.BaseConverter):
    accept_folder = True

    def handle_markdown_links(self, body: str) -> tuple[list, list]:
        # markdown style links
        note_links = []
        resources = []
        for link in common.get_markdown_links(body):
            if link.is_web_link or link.is_mail_link:
                continue  # keep the original links
            if link.url.endswith(".md"):
                # internal link
                note_links.append(
                    imf.NoteLink(str(link), Path(unquote(link.url)).stem, link.text)
                )
            else:
                # resource
                resources.append(
                    imf.Resource(self.root_path / link.url, str(link), link.text)
                )

        # qownnote style links
        for link in get_qownnote_links(body):
            note_links.append(imf.NoteLink(f"<{link}>", Path(unquote(link)).stem, link))

        return resources, note_links

    def parse_tags(self):
        """Parse tags from the sqlite DB."""
        assert self.root_path is not None
        db_file = self.root_path / "notes.sqlite"
        if not db_file.is_file():
            self.logger.debug(f"Couldn't find {db_file}")
            return {}

        tag_id_name_map = {}
        note_tag_map = defaultdict(list)
        conn = sqlite3.connect(db_file)
        try:
            cur = conn.cursor()

            # check version
            cur.execute("SELECT * FROM appData")
            for name, value in cur.fetchall():
                if name == "database_version" and value != "15":
                    self.logger.warning(f"Untested DB version {value}")

            # get tags
            cur.execute("SELECT * FROM tag")
            for tag_id, tag_name, *_ in cur.fetchall():
                tag_id_name_map[tag_id] = tag_name

            # get related notes and assign the tags
            cur.execute("SELECT * FROM noteTagLink")
            for _, tag_id, note_id, *_ in cur.fetchall():
                note_tag_map[note_id].append(imf.Tag(tag_id_name_map[tag_id], tag_id))
        except sqlite3.OperationalError as exc:
            self.logger.warning("Parsing the tag DB failed.")
            self.logger.debug(exc, exc_info=True)
            return {}
        finally:
            conn.close()
        return note_tag_map

    def convert(self, file_or_folder: Path):
        self.root_path = file_or_folder

        note_tag_map = self.parse_tags()

        for note_qownnotes in file_or_folder.glob("*.md"):
            title = note_qownnotes.stem
            self.logger.debug(f'Converting note "{title}"')
            note_body = note_qownnotes.read_text(encoding="utf-8")

            resources, note_links = self.handle_markdown_links(note_body)
            note_imf = imf.Note(
                title,
                "\n".join(note_body.split("\n")[3:]),  # TODO: make robust
                source_application=self.format,
                tags=note_tag_map.get(note_qownnotes.stem, []),
                resources=resources,
                note_links=note_links,
            )
            note_imf.time_from_file(note_qownnotes)
            self.root_notebook.child_notes.append(note_imf)
