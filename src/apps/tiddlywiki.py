"""Convert TiddlyWiki notes to the intermediate format."""

from datetime import datetime
import logging
from pathlib import Path
import json
from typing import List

import intermediate_format as imf


LOGGER = logging.getLogger("joplin_custom_importer")


def tiddlywiki_to_unix(tiddlywiki_time: str) -> int:
    """Format: https://tiddlywiki.com/static/DateFormat.html"""
    return int(datetime.strptime(tiddlywiki_time, "%Y%m%d%H%M%S%f").timestamp() * 1000)


def split_tags(tag_string: str) -> List[str]:
    """
    Tags are space separated. Tags with spaces are surrounded by double brackets.

    >>> split_tags("tag1 tag2 tag3 [[tag with spaces]]")
    ['tag1', 'tag2', 'tag3', 'tag with spaces']
    >>> split_tags("[[tag with spaces]]")
    ['tag with spaces']
    >>> split_tags("tag1 tag2 tag3")
    ['tag1', 'tag2', 'tag3']
    >>> split_tags("")
    []
    """
    if not tag_string.strip():
        return []
    space_splitted = tag_string.split(" ")
    final_tags = []
    space_separated_tag = ""
    for part in space_splitted:
        if space_separated_tag:
            if part.endswith("]]"):
                space_separated_tag += " " + part[:-2]
                final_tags.append(space_separated_tag)
                space_separated_tag = ""
            else:
                space_separated_tag += " " + part
        elif part.startswith("[["):
            space_separated_tag = part[2:]
        else:
            final_tags.append(part)
    return final_tags


def convert(file_: Path, parent: imf.Notebook):
    if file_.suffix.lower() != ".json":
        LOGGER.error("Unsupported format. Please export your tiddlers in JSON format.")
        return

    file_dict = json.loads(Path(file_).read_text(encoding="UTF-8"))
    for note_tiddlywiki in file_dict:
        note_joplin_data = {
            "title": note_tiddlywiki["title"],
            "body": note_tiddlywiki.get("text", ""),
            "author": note_tiddlywiki.get("creator", ""),
            "source_application": Path(__file__).stem,
        }
        if "created" in note_tiddlywiki:
            note_joplin_data["user_created_time"] = tiddlywiki_to_unix(
                note_tiddlywiki["created"]
            )
        if "modified" in note_tiddlywiki:
            note_joplin_data["user_updated_time"] = tiddlywiki_to_unix(
                note_tiddlywiki["modified"]
            )
        note_joplin = imf.Note(
            note_joplin_data,
            # Tags don't have a separate id. Just use the name as id.
            tags=[
                imf.Tag({"title": tag}, tag)
                for tag in split_tags(note_tiddlywiki.get("tags", ""))
            ],
        )
        if any(t.original_id.startswith("$:/tags/") for t in note_joplin.tags):
            continue  # skip notes with special tags
        parent.child_notes.append(note_joplin)
