"""Convert Google Keep notes to the intermediate format."""

from pathlib import Path
import json
import logging
import tarfile
import tempfile
import time
import zipfile

from intermediate_format import Note, Tag


LOGGER = logging.getLogger("joplin_custom_importer")


def convert(file_or_folder: Path, parent):
    if file_or_folder.suffix.lower() == ".zip":
        temp_folder = Path(tempfile.gettempdir()) / f"joplin_export_{int(time.time())}"
        with zipfile.ZipFile(file_or_folder) as zip_ref:
            zip_ref.extractall(temp_folder)
        input_folder = temp_folder
    elif file_or_folder.suffix.lower() == ".tgz":
        temp_folder = Path(tempfile.gettempdir()) / f"joplin_export_{int(time.time())}"
        with tarfile.open(file_or_folder) as tar_ref:
            tar_ref.extractall(temp_folder)
        input_folder = temp_folder
    elif file_or_folder.is_dir():
        input_folder = file_or_folder
    else:
        LOGGER.error("Unsupported format for Google Keep")
        return

    for file_ in input_folder.glob("**/*.json"):  # take only the exports in json format
        note_keep = json.loads(Path(file_).read_text(encoding="UTF-8"))
        tags_keep = [label["name"] for label in note_keep.get("labels", [])]
        resources_keep = []
        for resource_keep in note_keep.get("attachments", []):
            resources_keep.append(file_.parent.absolute() / resource_keep["filePath"])
        note_joplin = Note(
            {
                "title": note_keep["title"],
                "body": note_keep["textContent"],
                "user_created_time": note_keep["userEditedTimestampUsec"] // 1000,
                "user_updated_time": note_keep["userEditedTimestampUsec"] // 1000,
                "source_application": Path(__file__).stem,
            },
            # Labels / tags don't have a separate id. Just use the name as id.
            tags=[Tag({"title": tag}, tag) for tag in tags_keep],
            resources=resources_keep,
        )
        parent.child_notes.append(note_joplin)
