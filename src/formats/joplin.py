"""Convert Joplin notes to the intermediate format."""

from collections import defaultdict
import datetime as dt
import enum
import math
from pathlib import Path

import converter
import intermediate_format as imf
import markdown_lib


class ItemType(enum.IntEnum):
    # https://joplinapp.org/api/references/rest_api/#item-type-ids
    NOTE = 1
    FOLDER = 2
    SETTING = 3
    RESOURCE = 4
    TAG = 5
    NOTE_TAG = 6
    SEARCH = 7
    ALARM = 8
    MASTER_KEY = 9
    ITEM_CHANGE = 10
    NOTE_RESOURCE = 11
    RESOURCE_LOCAL_STATE = 12
    REVISION = 13
    MIGRATION = 14
    SMART_FILTER = 15
    COMMAND = 16


def handle_markdown_links(
    body: str, resource_id_filename_map: dict
) -> tuple[imf.Resources, imf.NoteLinks]:
    note_links = []
    resources = []
    for link in markdown_lib.common.get_markdown_links(body):
        if link.is_web_link or link.is_mail_link:
            continue  # keep the original links
        resource_path = resource_id_filename_map.get(link.url[2:])
        if resource_path is None:
            # internal link
            note_links.append(imf.NoteLink(str(link), link.url[2:], link.text))
        else:
            # resource
            resources.append(imf.Resource(resource_path, str(link), link.text))
    return resources, note_links


class Converter(converter.BaseConverter):
    accepted_extensions = [".jex"]

    def parse_data(self):
        # pylint: disable=too-many-locals
        parent_id_note_map = []
        parent_id_notebook_map = []
        resource_id_filename_map = {}
        available_tags = []
        note_tag_id_map = defaultdict(list)
        for file_ in sorted(self.root_path.rglob("*.md")):
            markdown_raw = file_.read_text(encoding="utf-8")
            try:
                markdown, metadata_raw = markdown_raw.rsplit("\n\n", 1)
            except ValueError:
                markdown = ""
                metadata_raw = markdown_raw
            metadata_json = {}
            for line in metadata_raw.split("\n"):
                key, value = line.split(": ", 1)
                metadata_json[key] = value

            # https://joplinapp.org/help/api/references/rest_api/#item-type-ids
            type_ = ItemType(int(metadata_json["type_"]))
            if type_ == ItemType.NOTE:
                title, body = markdown_lib.common.split_h1_title_from_body(markdown)
                self.logger.debug(f'Converting note "{title}"')
                note_imf = imf.Note(
                    title.strip(),
                    body.strip(),
                    created=dt.datetime.fromisoformat(metadata_json["created_time"]),
                    updated=dt.datetime.fromisoformat(metadata_json["updated_time"]),
                    # TODO: How to handle todos?
                    # is_todo=bool(int(metadata_json.get("is_todo", 0))),
                    # completed=bool(
                    #     int(metadata_json.get("todo_completed", False))
                    # ),
                    # due=int(metadata_json.get("todo_due", 0)),
                    author=metadata_json.get("author") or None,
                    source_application=self.format,
                    original_id=metadata_json["id"],
                )
                # not set is exported as 0.0
                for key in ("latitude", "longitude", "altitude"):
                    if (val := metadata_json.get(key)) is not None and not math.isclose(
                        val_float := float(val), 0.0
                    ):
                        setattr(note_imf, key, val_float)
                parent_id_note_map.append((metadata_json["parent_id"], note_imf))
            elif type_ == ItemType.FOLDER:
                parent_id_notebook_map.append(
                    (
                        metadata_json["parent_id"],
                        imf.Notebook(markdown.strip(), original_id=metadata_json["id"]),
                    )
                )
            elif type_ == ItemType.RESOURCE:
                # TODO: some metadata is lost
                filename = Path(metadata_json["id"]).with_suffix(
                    "." + metadata_json["file_extension"]
                )
                resource_id_filename_map[metadata_json["id"]] = (
                    self.root_path / "resources" / filename
                )
            elif type_ == ItemType.TAG:
                available_tags.append(
                    imf.Tag(markdown.strip(), original_id=metadata_json["id"])
                )
            elif type_ == ItemType.NOTE_TAG:
                note_tag_id_map[metadata_json["note_id"]].append(
                    metadata_json["tag_id"]
                )
            else:
                self.logger.debug(f"Ignoring note type {type_}")
        return (
            parent_id_note_map,
            parent_id_notebook_map,
            resource_id_filename_map,
            available_tags,
            note_tag_id_map,
        )

    def convert_data(
        self,
        parent_id_note_map,
        parent_id_notebook_map,
        resource_id_filename_map,
        available_tags,
        note_tag_id_map,
    ):  # pylint: disable=too-many-arguments
        for parent_id, note in parent_id_note_map:
            # assign tags
            assert note.original_id is not None
            for tag_id in note_tag_id_map.get(note.original_id, []):
                for tag in available_tags:
                    if tag.original_id == tag_id:
                        note.tags.append(tag)
                        break
            # resources and internal links
            resources, note_links = handle_markdown_links(
                note.body, resource_id_filename_map
            )
            note.resources = resources
            note.note_links = note_links
            # assign to parent notebook
            for _, notebook in parent_id_notebook_map:
                if notebook.original_id == parent_id:
                    notebook.child_notes.append(note)
                    break

        # span the notebook tree
        for parent_id, notebook in parent_id_notebook_map:
            if parent_id:
                for _, parent_notebook in parent_id_notebook_map:
                    if parent_notebook.original_id == parent_id:
                        parent_notebook.child_notebooks.append(notebook)
                        break
            else:
                self.root_notebook.child_notebooks.append(notebook)

    def convert(self, file_or_folder: Path):
        data = self.parse_data()
        self.convert_data(*data)
