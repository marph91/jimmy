"""Convert xit notes to the intermediate format."""

from pathlib import Path

# from stage_left import parse_text
# from stage_left.types import State

# import common
import converter
# import intermediate_format as imf


class Converter(converter.BaseConverter):
    accepted_extensions = [".xit"]

    def convert(self, file_or_folder: Path):
        return  # TODO: implement a checklist based approach

        # groups = parse_text(file_or_folder.read_text(encoding="utf-8"))
        # for group in groups:
        #     group_notebook = imf.Notebook(
        #         group.title if group.title else "Unnamed Group"
        #     )

        #     for item in group.items:
        #         note_data = {
        #             "title": item.format_description(
        #                 normalize_whitespace=True,
        #                 with_priority=False,
        #                 with_tags=False,
        #                 with_due_date=False,
        #             ),
        #             "is_todo": 1,
        #             "source_application": self.format,
        #         }
        #         if item.state in (State.CHECKED, State.OBSOLETE):
        #             note_data["completed"] = common.current_unix_ms()
        #         if item.due_date:
        #             note_data["due"] = common.date_to_unix_ms(item.due_date)

        #         tags_string = []
        #         for tag in item.tags:
        #             if tag.key is None:
        #                 tags_string.append(tag.value)
        #             else:
        #                 tags_string.append(f"{tag.key}={tag.value}")
        #         if item.priority:
        #             tags_string.append(f"xit-priority-{item.priority}")

        #         note = imf.Note(
        #             **note_data, tags=[imf.Tag(tag) for tag in tags_string])
        #         group_notebook.child_notes.append(note)
        #     self.root_notebook.child_notebooks.append(group_notebook)
