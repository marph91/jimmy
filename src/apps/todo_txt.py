"""Convert todo.txt tasks to the intermediate format."""

from pathlib import Path

import pytodotxt

from common import current_unix_ms, date_to_unix_ms, iso_to_unix_ms
from intermediate_format import Note, Notebook, Tag


def convert(file_: Path, parent: Notebook):
    todotxt = pytodotxt.TodoTxt(file_)
    todotxt.parse()

    for task in todotxt.tasks:
        note_data = {
            "title": task.bare_description(),
            "is_todo": 1,
            "source_application": Path(__file__).stem,
        }
        if task.creation_date is not None:
            note_data["user_creation_date"] = date_to_unix_ms(task.creation_date)
        if task.is_completed:
            note_data["todo_completed"] = (
                current_unix_ms()
                if task.completion_date is None
                else date_to_unix_ms(task.completion_date)
            )

        for key, value in task.attributes.items():
            # "value" is a list, because there can be multiple attributes with the same key.
            # For example: "due:1 due:2" will get parsed as "due: [1, 2]".
            # Just take the first one for simplicity.
            if key == "due":
                note_data["todo_due"] = iso_to_unix_ms(value[0])
            else:
                print("ignoring unsupported key {key}")

        tags_string = []
        if task.priority is not None:
            tags_string += [f"todotxt-priority-{task.priority}"]
        tags_string += [f"todotxt-context-{context}" for context in task.contexts]
        tags_string += [f"todotxt-project-{project}" for project in task.projects]

        joplin_note = Note(
            note_data, tags=[Tag({"title": tag}, tag) for tag in tags_string]
        )
        parent.child_notes.append(joplin_note)
        print(joplin_note)
