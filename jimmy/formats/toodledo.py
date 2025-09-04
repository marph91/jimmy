"""Convert toodledo tasks to the intermediate format."""

# import csv
import datetime as dt
from pathlib import Path

from jimmy import common, converter, intermediate_format as imf


def parse_date(date_: str, time_: str = "") -> dt.datetime | None:
    """
    >>> parse_date("", "")
    >>> parse_date("2028-09-07")
    datetime.datetime(2028, 9, 7, 0, 0)
    >>> parse_date("2028-09-07", "")
    datetime.datetime(2028, 9, 7, 0, 0)
    >>> parse_date("2024-04-27", "8:00 pm")
    datetime.datetime(2024, 4, 27, 8, 0)
    """
    if not date_:
        return None
    if time_:
        datetime_ = dt.datetime.strptime(date_ + " " + time_, "%Y-%m-%d %H:%M %p")
    else:
        datetime_ = dt.datetime.strptime(date_, "%Y-%m-%d")
    return datetime_


class Converter(converter.BaseConverter):
    # accepted_extensions = [".csv"]

    def find_parent_notebook(self, notebook_name, current_notebook):
        for notebook in current_notebook.child_notebooks:
            if notebook.title == notebook_name:
                return notebook
            matching_nested_notebook = self.find_parent_notebook(
                notebook_name, current_notebook=notebook
            )
            if matching_nested_notebook is not None:
                return matching_nested_notebook
        return None

    def parse_tasks(self, reader):
        for row in reader:
            # unused data:
            # row["LOCATION"]
            # row["REPEAT"]
            # row["LENGTH"]
            # row["TIMER"]

            # tags
            tags = row["TAG"].split(",") if row["TAG"] else []
            contexts = row["CONTEXT"].split(",") if row["CONTEXT"] else []
            tags.extend([f"toodledo-context-{context}" for context in contexts])
            goals = row["GOAL"].split(",") if row["GOAL"] else []
            tags.extend([f"toodledo-goal-{goal}" for goal in goals])
            priority = row["PRIORITY"] if row["PRIORITY"] else 0
            tags.append(f"toodledo-priority-{priority}")
            if row["STAR"] == "Yes":
                tags.append("toodledo-starred")
            if row["STATUS"]:
                tags.append(f"toodledo-status-{row['STATUS']}")

            note_data = {
                "title": row["TASK"],
                "body": row["NOTE"],
                # "is_todo": 1,
                "source_application": self.format,
            }
            if (due_date := parse_date(row["DUEDATE"], row["DUETIME"])) is not None:
                note_data["due"] = common.datetime_to_ms(due_date)
            if (start_date := parse_date(row["STARTDATE"], row["STARTTIME"])) is not None:
                note_data["created"] = common.datetime_to_ms(start_date)
            completed_date_string = row.get("COMPLETED", "")
            if (completed_date := parse_date(completed_date_string)) is not None:
                note_data["completed"] = common.datetime_to_ms(completed_date)
            joplin_note = imf.Note(**note_data, tags=[imf.Tag(tag) for tag in tags])

            if not row["FOLDER"]:
                parent_notebook = self.root_notebook
            else:
                parent_notebook = self.find_parent_notebook(row["FOLDER"], self.root_notebook)
                if parent_notebook is None:
                    parent_notebook = imf.Notebook(row["FOLDER"])
                    self.root_notebook.child_notebooks.append(parent_notebook)
            parent_notebook.child_notes.append(joplin_note)

    def parse_notebooks(self, reader):
        for row in reader:
            note_data = {
                "title": row["TITLE"],
                "body": row["NOTE"],
                "source_application": self.format,
            }
            if (created_time := parse_date(row["ADDED"])) is not None:
                note_data["created"] = common.datetime_to_ms(created_time)
            if (updated_time := parse_date(row["MODIFIED"])) is not None:
                note_data["updated"] = common.datetime_to_ms(updated_time)
            joplin_note = imf.Note(**note_data)

            if not row["FOLDER"]:
                parent_notebook = self.root_notebook
            else:
                parent_notebook = self.find_parent_notebook(row["FOLDER"], self.root_notebook)
                if parent_notebook is None:
                    parent_notebook = imf.Notebook(row["FOLDER"])
                    self.root_notebook.child_notebooks.append(parent_notebook)
            parent_notebook.child_notes.append(joplin_note)

    def convert(self, file_or_folder: Path):
        return  # TODO: implement a checklist based approach

        # with open(file_or_folder, encoding="utf-8") as csvfile:
        #     reader = csv.DictReader(csvfile)

        #     # Guess the export type based on the file name.
        #     if file_or_folder.stem.startswith("toodledo_current"):
        #         return self.parse_tasks(reader)
        #     if file_or_folder.stem.startswith("toodledo_completed"):
        #         return self.parse_tasks(reader)
        #     if file_or_folder.stem.startswith("toodledo_notebook"):
        #         return self.parse_notebooks(reader)
        #     self.logger.error("Unsupported format for toodledo")
        #     return None
