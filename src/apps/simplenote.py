"""Convert simplenote notes to the intermediate format."""

import json
import logging
from pathlib import Path
import zipfile

import common
import intermediate_format as imf


LOGGER = logging.getLogger("joplin_custom_importer")


def convert(zip_or_folder: Path, parent: imf.Notebook):
    if zip_or_folder.suffix.lower() == ".zip":
        with zipfile.ZipFile(zip_or_folder) as zip_ref, zip_ref.open(
            "source/notes.json"
        ) as zipped_json:
            input_json = json.loads(zipped_json.read().decode("UTF-8"))
    elif zip_or_folder.is_dir():
        input_json = json.loads((zip_or_folder / "source/notes.json").read_text())
    else:
        LOGGER.error("Unsupported format for simplenote")
        return

    for note_simplenote in input_json["activeNotes"]:
        # title is the first line
        title, body = note_simplenote["content"].split("\n", maxsplit=1)

        note_links = []
        for description, url in common.get_markdown_links(body):
            if url.startswith("http"):
                continue  # web link
            elif url.startswith("simplenote://"):
                # internal link
                _, linked_note_id = url.rsplit("/", 1)
                note_links.append(
                    imf.NoteLink(f"[{description}]({url})", linked_note_id, description)
                )
        note_joplin = imf.Note(
            {
                "title": title.strip(),
                "body": body.lstrip(),
                "user_created_time": common.iso_to_unix_ms(
                    note_simplenote["creationDate"]
                ),
                "user_updated_time": common.iso_to_unix_ms(
                    note_simplenote["lastModified"]
                ),
                "source_application": Path(__file__).stem,
            },
            # Tags don't have a separate id. Just use the name as id.
            tags=[imf.Tag({"title": tag}, tag) for tag in note_simplenote["tags"]],
            note_links=note_links,
            original_id=note_simplenote["id"],
        )
        parent.child_notes.append(note_joplin)
