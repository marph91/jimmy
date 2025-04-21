"""Convert todoist tasks to the intermediate format."""

# import csv
from datetime import datetime
from pathlib import Path

# import common
from jimmy import converter
# import intermediate_format as imf


def parse_author(author_string: str) -> str:
    """
    >>> parse_author("")
    ''
    >>> parse_author("Dieter (123)")
    'Dieter'
    """
    return author_string.rsplit(" (", 1)[0]


def parse_date(date_string: str | None) -> datetime | None:
    """
    # datetime.datetime({datetime.today().year}, 2, 29, 0, 0)
    # >>> parse_date("10 Apr 17:15")
    # datetime.datetime({datetime.today().year}, 4, 10, 17, 15)
    # >>> parse_date("2 Jan 2025")
    >>> parse_date("")
    >>> parse_date("29 Feb 2024")
    datetime.datetime(2024, 2, 29, 0, 0)
    >>> parse_date("2 Jan 2026 09:35")
    datetime.datetime(2026, 1, 2, 9, 35)
    >>> parse_date("123")
    """
    # docstring can't be f-string, so two test cases need to be skipped.
    # See: https://stackoverflow.com/a/70865657/7410886
    if not date_string:
        return None

    def try_strptime(format_: str) -> datetime | None:
        try:
            if "%Y" in format_:
                parsed_date = datetime.strptime(date_string, format_)
            else:
                # When the year is missing, we need to insert it manually
                # to avoid issues with leap days.
                # See https://stackoverflow.com/a/18369590/7410886.
                parsed_date = datetime.strptime(
                    str(datetime.today().year) + " " + date_string, "%Y " + format_
                )
            return parsed_date
        except ValueError:
            return None

    # TODO: Ignoring the locale column could yield problems.
    possible_date_formats = (
        # some date this year
        "%d %b",
        # some date this year with time
        "%d %b %H:%M",
        # some date next year
        "%d %b %Y",
        # some date in future with time
        "%d %b %Y %H:%M",
    )
    for format_ in possible_date_formats:
        if (datetime_object := try_strptime(format_)) is not None:
            return datetime_object
    return None


def split_labels(title_labels: str) -> tuple[str, list[str]]:
    """
    >>> split_labels("")
    ('', [])
    >>> split_labels("Note without labels")
    ('Note without labels', [])
    >>> split_labels("Note with @label")
    ('Note with', ['label'])
    >>> split_labels("Note with @multiple @labels")
    ('Note with', ['multiple', 'labels'])
    """
    title = []
    labels = []
    for part in title_labels.split(" "):
        if part.startswith("@"):
            labels.append(part[1:])
        else:
            title.append(part)
    return " ".join(title), labels


class Converter(converter.BaseConverter):
    accepted_extensions = [".csv"]

    def convert(self, file_or_folder: Path):
        return  # TODO: implement a checklist based approach

        # # - Finished tasks don't get exported.
        # # - Todoist titles can be markdown formatted. Joplin titles are not.
        # #   If imported as task list, we would gain markdown and sub-tasks,
        # #   but lose the due date and priority tags.

        # project_notebook = imf.Notebook(file_or_folder.stem)
        # self.root_notebook.child_notebooks.append(project_notebook)
        # current_section = project_notebook
        # # "utf-8-sig" to prevent "\ufeffTYPE"
        # with open(file_or_folder, encoding="utf-8-sig") as csvfile:
        #     reader = csv.DictReader(csvfile)
        #     for row in reader:
        #         if row["TYPE"] == "section":
        #             current_section = imf.Notebook(row["CONTENT"])
        #             project_notebook.child_notebooks.append(current_section)
        #         elif row["TYPE"] == "task":
        #             title, labels = split_labels(row["CONTENT"])
        #             note_data = {
        #                 "title": title,
        #                 "body": row["DESCRIPTION"],
        #                 "author": parse_author(row["AUTHOR"]),
        #                 "is_todo": 1,
        #                 "source_application": self.format,
        #             }
        #             if (due_date := parse_date(row["DATE"])) is not None:
        #                 note_data["due"] = common.datetime_to_ms(due_date)

        #             tags_string = [*labels, f"todoist-priority-{row['PRIORITY']}"]
        #             joplin_note = imf.Note(
        #                 **note_data,
        #                 tags=[imf.Tag(tag) for tag in tags_string],
        #             )
        #             current_section.child_notes.append(joplin_note)
        #         elif row["TYPE"] == "":
        #             continue  # ignore empty rows
        #         else:
        #             self.logger.debug(f"Ignoring unknown type: {row['TYPE']}")
