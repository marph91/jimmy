from pathlib import Path
import json

from common import Note, Tag


def convert(file_: Path, root):
    # https://clipto.pro/
    # export only possible in android app:
    # - https://github.com/clipto-pro/Desktop/issues/21#issuecomment-537401330
    # - settings -> time machine -> backup to file
    # import:
    # - notes
    # - tags

    file_dict = json.loads(Path(file_).read_text(encoding="UTF-8"))
    tags = []
    # tags are contained in filters
    for filter_ in file_dict.get("filters"):
        tags.append(Tag({"title": filter_["name"]}, filter_["uid"]))

    joplin_notes = []
    for note in file_dict.get("notes", []):
        note_joplin = Note(
            {"title": note["title"], "body": note["text"]}, tags=note["tagIds"]
        )
        joplin_notes.append(note_joplin)
        print(note_joplin)

    root.child_notes = joplin_notes
    return root, tags
