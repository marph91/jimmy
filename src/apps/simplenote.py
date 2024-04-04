"""Convert simplenote notes to the intermediate format."""

import json
from pathlib import Path
import zipfile

from common import iso_to_unix_ms
from intermediate_format import Note, Tag


def convert(input_zip: Path, parent):
    # TODO: note links - probably second pass and map old uid - joplin uid?

    with zipfile.ZipFile(input_zip) as zip_ref, zip_ref.open(
        "source/notes.json"
    ) as zipped_json:
        notes_simplenote = json.loads(zipped_json.read().decode("UTF-8"))
        for note_simplenote in notes_simplenote["activeNotes"]:
            # title is the first line
            title, body = note_simplenote["content"].split("\n", maxsplit=1)
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
                    "source_application": Path(__file__).stem,
                },
                # Tags don't have a separate id. Just use the name as id.
                tags=[Tag({"title": tag}, tag) for tag in note_simplenote["tags"]],
            )
            parent.child_notes.append(note_joplin)
            print(note_joplin)

    return parent
