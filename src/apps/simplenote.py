"""Convert simplenote notes to the intermediate format."""

import json
from pathlib import Path
import zipfile

from common import iso_to_unix_ms
from intermediate_format import Note, Tag


def convert(input_zip: Path, parent):
    # TODO: note links - probably second pass and map old uid - joplin uid?

    all_tags = set()
    with zipfile.ZipFile(input_zip) as zip_ref, zip_ref.open(
        "source/notes.json"
    ) as zipped_json:
        notes_simplenote = json.loads(zipped_json.read().decode("UTF-8"))
        for note_simplenote in notes_simplenote["activeNotes"]:
            # title is the first line
            title, body = note_simplenote["content"].split("\n", maxsplit=1)
            tags = note_simplenote["tags"]
            note_joplin = Note(
                {
                    "title": title.strip(),
                    "body": body.lstrip(),
                    "user_created_time": iso_to_unix_ms(
                        note_simplenote["creationDate"]
                    ),
                    "user_updated_time": iso_to_unix_ms(
                        note_simplenote["lastModified"]
                    ),
                },
                tags=tags,
            )
            parent.child_notes.append(note_joplin)
            all_tags.update(tags)
            print(note_joplin)

    # labels in simplenote don't have a separate uid. just use the name as id
    tags_joplin = [Tag({"title": tag}, tag) for tag in all_tags]
    return parent, tags_joplin
