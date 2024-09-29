"""Convert Zoho Notebook notes to the intermediate format."""

import datetime as dt
import json
from pathlib import Path

from bs4 import BeautifulSoup

import common
import converter
import intermediate_format as imf


def clean_tables(soup):
    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            for td in row.find_all("td"):
                # remove all tags from table data
                text_only = td.text
                td.clear()
                td.append(text_only)
        # tables seem to be headerless always
        #         # make first row to header
        #         if row_index == 0:
        #             td.name = "th"
        # # remove "tbody"
        # body = table.find("tbody")
        # body.unwrap()


def clean_task_lists(soup):
    # TODO: Not sure why the cleaned task lists still don't work.
    # It works online. Maybe caused by an old pandoc version.
    for task_list in soup.find_all("div", class_="checklist"):
        task_list.name = "ul"
        # remove the spans
        for span in task_list.find_all("span"):
            span.unwrap()
        # remove the first divs
        for child in task_list.children:
            child.unwrap()
        # convert the second divs to list items
        for child in task_list.children:
            child.name = "li"


class Converter(converter.BaseConverter):
    accepted_extensions = [".zip"]

    def prepare_input(self, input_: Path) -> Path:
        unzipped_input = common.extract_zip(input_)
        # There is always one subfolder that contains all data.
        return common.get_single_child_folder(unzipped_input)

    def parse_links(self, note_body: str):
        resources = []
        note_links = []
        for link in common.get_markdown_links(note_body):
            if link.is_web_link or link.is_mail_link:
                continue  # keep the original links
            if link.url.startswith("zohonotebook://"):
                # internal link
                _, linked_note_id = link.url.rsplit("/", 1)
                note_links.append(
                    imf.NoteLink(
                        str(link),
                        linked_note_id,
                        # TODO: seems like internal links are always named "link"
                        link.text,
                    )
                )
            elif (self.root_path / link.url).is_file():
                # resource
                resources.append(
                    imf.Resource(self.root_path / link.url, str(link), link.text)
                )
        return resources, note_links

    def convert_note(self, file_: Path):
        soup = BeautifulSoup(file_.read_text(encoding="utf-8"), "html.parser")

        # parse metadata and convert it to the intermediate format
        metadata = {}
        if soup.body is not None:
            for key, value in soup.body.attrs.items():
                metadata[key] = json.loads(value)

        title = metadata["data-notecard"]["name"]
        self.logger.debug(f'Converting note "{title}"')

        # get or find parent notebook
        # Assume that notebooks can't be nested.
        notebook_imf = imf.Notebook(
            metadata["data-notebook"]["name"],
            created=dt.datetime.fromisoformat(
                metadata["data-notebook"]["created_date"]
            ),
            updated=dt.datetime.fromisoformat(
                metadata["data-notebook"]["modified_date"]
            ),
        )
        parent_notebook = None
        for potential_parent in self.root_notebook.child_notebooks:
            # TODO: Is there a notebook ID? We just identify by name and creation date.
            if (
                potential_parent.title == notebook_imf.title
                and potential_parent.created == notebook_imf.created
                and potential_parent.updated == notebook_imf.updated
            ):
                # Use the existing notebook if possible.
                parent_notebook = potential_parent
                break

        # If there is no matching parent, create one.
        if parent_notebook is None:
            parent_notebook = notebook_imf
            self.root_notebook.child_notebooks.append(parent_notebook)

        # note metadata
        # TODO: optionally handle color

        # TODO: How to handle remainder?
        # if (reminders := metadata.get("data-remainder")) is not None:
        #     # There seem to be possibly multiple reminders, but we can handle
        #     # only one. Take the first one.
        #     note_data["is_todo"] = True
        #     note_data["created"] = dt.datetime.fromisoformat(
        #         reminders[0]["ZReminderTime"]
        #     )
        #     if bool(int(reminders[0]["is-completed"])):
        #         note_data["completed"] = True
        #         # There isn't a due time. Just take the last modified time.
        #         note_data["due"] = dt.datetime.fromisoformat(
        #             reminders[0]["modified-time"]
        #         )

        # convert the note body to Markdown
        # TODO:
        # - checklists are note working, even with "+task_lists"
        # - tables are not working
        if soup.body is not None:
            clean_tables(soup)
            clean_task_lists(soup)
            body = common.markup_to_markdown(str(soup))

            # resources and internal links
            resources, note_links = self.parse_links(body)
        else:
            resources, note_links = [], []

        # create note
        note_imf = imf.Note(
            title,
            body,
            created=dt.datetime.fromisoformat(
                metadata["data-notecard"]["created_date"]
            ),
            updated=dt.datetime.fromisoformat(
                metadata["data-notecard"]["modified_date"]
            ),
            source_application=self.format,
            tags=[imf.Tag(tag) for tag in metadata.get("data-tag", [])],
            resources=resources,
            note_links=note_links,
            original_id=file_.stem,
        )
        parent_notebook.child_notes.append(note_imf)

    def convert(self, file_or_folder: Path):
        self.root_path = self.prepare_input(file_or_folder)

        for item in self.root_path.iterdir():
            if item.suffix != ".html" or item.name == "index.html":
                continue  # we want only the notes

            self.convert_note(item)
