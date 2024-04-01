from pathlib import Path
import json
import tarfile
import tempfile
import time
import zipfile

from common import Note, Tag


def convert(file_or_folder: Path, root):
    # export via takeout:
    # https://www.howtogeek.com/694042/how-to-export-your-google-keep-notes-and-attachments/

    if file_or_folder.suffix == ".zip":
        temp_folder = Path(tempfile.gettempdir()) / f"joplin_export_{int(time.time())}"
        with zipfile.ZipFile(file_or_folder) as zip_ref:
            zip_ref.extractall(temp_folder)
        input_folder = temp_folder
    elif file_or_folder.suffix == ".tgz":
        temp_folder = Path(tempfile.gettempdir()) / f"joplin_export_{int(time.time())}"
        with tarfile.open(file_or_folder) as tar_ref:
            tar_ref.extractall(temp_folder)
        input_folder = temp_folder
    elif file_or_folder.is_dir():
        input_folder = file_or_folder
    else:
        print("Unsupported format for Google Keep")
        return root, []

    tags_keep_all_notes = set()
    notes_joplin = []
    for file_ in input_folder.glob("**/*.json"):  # take only the exports in json format
        if file_.suffix == ".json":
            note_keep = json.loads(Path(file_).read_text(encoding="UTF-8"))
            tags_keep = [label["name"] for label in note_keep.get("labels", [])]
            resources_keep = []
            for resource_keep in note_keep.get("attachments", []):
                resources_keep.append(
                    file_.parent.absolute() / resource_keep["filePath"]
                )
            note_joplin = Note(
                {"title": note_keep["title"], "body": note_keep["textContent"]},
                tags=tags_keep,
                resources=resources_keep,
            )
            notes_joplin.append(note_joplin)
            tags_keep_all_notes.update(tags_keep)
            print(note_joplin)

    # labels in keep don't have a separate uid. just use the name as id
    tags_joplin = [Tag({"title": tag}, tag) for tag in tags_keep_all_notes]

    root.child_notes = notes_joplin
    return root, tags_joplin
