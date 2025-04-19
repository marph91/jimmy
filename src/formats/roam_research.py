"""Convert a Roam Research graph to the intermediate format."""

import json
from pathlib import Path

import common
import converter
import intermediate_format as imf
import markdown_lib.common
from markdown_lib.roam_research import roam_to_md


class Converter(converter.BaseConverter):
    accepted_extensions = [".json"]  # TODO: json or zip?

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.block_id_page_id_map = {}
        self.page_title_page_id_map = {}

    def parse_children(self, children, level=0):
        body_roam = []
        block_uids = []

        for child in children:
            string_ = child["string"]
            block_uids.append(child["uid"])

            if (heading_level := child.get("heading")) is not None:
                # Reset indentation level at heading.
                # Else the next lines would be rendered as code.
                prefix = "#" * heading_level + " "
                level = -1
            elif string_.strip() == "---":
                prefix = ""
                level = -1
            elif (
                string_.startswith("```")
                and string_.endswith("```")
                and string_[-4] != "\n"
            ):
                string_ = string_[:-3] + "\n" + string_[-3:]
                prefix = ""
            else:
                prefix = " " * 4 * level + "- "

            body_roam.append(prefix + string_)
            child_body_roam, child_block_uids = self.parse_children(
                child.get("children", []), level=level + 1
            )
            body_roam.extend(child_body_roam)
            block_uids.extend(child_block_uids)
        return body_roam, block_uids

    @common.catch_all_exceptions
    def convert_note(self, page):
        # title is the first line
        title = page["title"].strip()
        self.logger.debug(f'Converting note "{title}"')

        note_imf = imf.Note(
            title,
            created=common.timestamp_to_datetime(
                page.get("create-time", page["edit-time"]) // (10**3)
            ),
            updated=common.timestamp_to_datetime(page["edit-time"] // (10**3)),
            original_id=page["uid"],
            source_application=self.format,
            # TODO: are there resources?
        )

        body_roam, block_ids = self.parse_children(page.get("children", []))

        # for later note linking
        for block_id in block_ids:
            self.block_id_page_id_map[block_id] = page["uid"]
        self.page_title_page_id_map[title] = page["uid"]

        body_md = roam_to_md("\n".join(body_roam))
        note_imf.body = body_md

        inline_tags = markdown_lib.common.get_inline_tags(note_imf.body, ["#"])
        note_imf.tags = [imf.Tag(tag) for tag in inline_tags]

        self.root_notebook.child_notes.append(note_imf)

    def add_note_links(self, root_notebook: imf.Notebook | None = None):
        # TODO: helper function for getting all notes?
        if root_notebook is None:
            root_notebook = self.root_notebook

        for notebook in root_notebook.child_notebooks:
            self.add_note_links(notebook)

        for note in root_notebook.child_notes:
            for link in markdown_lib.common.get_markdown_links(note.body):
                if link.is_web_link or link.is_mail_link:
                    continue  # keep the original links
                if link.url.startswith("roam-page://"):
                    linked_page_title = link.url[len("roam-page://") :]
                    if (
                        linked_page_id := self.page_title_page_id_map.get(
                            linked_page_title
                        )
                    ) is not None:
                        note.note_links.append(
                            imf.NoteLink(str(link), linked_page_id, link.text)
                        )
                    else:
                        self.logger.debug(
                            f'Page with title "{linked_page_title}" not found.'
                        )
                elif link.url.startswith("roam-block://"):
                    # just link to page
                    linked_block_id = link.url[len("roam-block://") :]
                    if (
                        linked_page_id := self.block_id_page_id_map.get(linked_block_id)
                    ) is not None:
                        note.note_links.append(
                            imf.NoteLink(str(link), linked_page_id, link.text)
                        )
                    else:
                        self.logger.debug(f"Block ID {linked_block_id} not found.")

    def convert(self, file_or_folder: Path):
        input_json = json.loads(file_or_folder.read_text(encoding="utf-8"))

        for page in input_json:
            self.convert_note(page)

        # There are many empty notes, but don't remove them,
        # since this would break links.
        # self.remove_empty_notes()

        # second pass: add note links
        self.add_note_links()
