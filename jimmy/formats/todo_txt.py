"""Convert todo.txt tasks to the intermediate format."""

# import datetime as dt
from pathlib import Path

# import pytodotxt

# import common
from jimmy import converter
# import intermediate_format as imf


class Converter(converter.BaseConverter):
    # accepted_extensions = [".txt"]

    def convert(self, file_or_folder: Path):
        return  # TODO: implement a checklist based approach

        # todotxt = pytodotxt.TodoTxt(file_or_folder)
        # todotxt.parse()

        # for task in todotxt.tasks:
        #     note_data = {
        #         "title": task.bare_description(),
        #         "is_todo": 1,
        #         "source_application": self.format,
        #     }
        #     if task.creation_date is not None:
        #         note_data["created"] = common.date_to_unix_ms(task.creation_date)
        #     if task.is_completed:
        #         note_data["completed"] = (
        #             common.current_unix_ms()
        #             if task.completion_date is None
        #             else common.date_to_unix_ms(task.completion_date)
        #         )

        #     for key, value in task.attributes.items():
        #         # "value" is a list, because there can be multiple attributes with the
        #         # same key. For example: "due:1 due:2" will get parsed as
        #         # "due: [1, 2]".
        #         # Just take the first one for simplicity.
        #         if key == "due":
        #             note_data["due"] = common.iso_to_datetime(value[0])
        #         else:
        #             self.logger.debug(f"ignoring unsupported key {key}")

        #     tags_string = []
        #     if task.priority is not None:
        #         tags_string += [f"todotxt-priority-{task.priority}"]
        #     tags_string += [f"todotxt-context-{context}" for context in task.contexts]
        #     tags_string += [f"todotxt-project-{project}" for project in task.projects]

        #     joplin_note = imf.Note(
        #         **note_data, tags=[imf.Tag(tag) for tag in tags_string]
        #     )
        #     self.root_notebook.child_notes.append(joplin_note)
