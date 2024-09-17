"""Convert Joplin notes to the intermediate format."""

from collections import defaultdict
import enum
from pathlib import Path

import common
import converter
import intermediate_format as imf


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
) -> tuple[list, list]:
    note_links = []
    resources = []
    for link in common.get_markdown_links(body):
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

    def prepare_input(self, input_: Path) -> Path:
        return common.extract_tar(input_)

    def parse_data(self, file_or_folder: Path):
        # pylint: disable=too-many-locals
        self.root_path = self.prepare_input(file_or_folder)

        parent_id_note_map = []
        parent_id_notebook_map = []
        resource_id_filename_map = {}
        available_tags = []
        note_tag_id_map = defaultdict(list)
        for file_ in self.root_path.glob("**/*.md"):
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
                title, body = common.split_h1_title_from_body(markdown)
                data = {
                    "title": title.strip(),
                    "body": body.strip(),
                    "user_created_time": common.iso_to_unix_ms(
                        metadata_json["created_time"]
                    ),
                    "user_updated_time": common.iso_to_unix_ms(
                        metadata_json["updated_time"]
                    ),
                    "is_todo": bool(int(metadata_json.get("is_todo", 0))),
                    "todo_completed": bool(
                        int(metadata_json.get("todo_completed", False))
                    ),
                    "todo_due": int(metadata_json.get("todo_due", 0)),
                    "source_application": self.format,
                }
                for key in ("latitude", "longitude", "altitude"):
                    if (value := metadata_json.get(key)) is not None:
                        data[key] = float(value)
                # TODO: Not represented in frontmatter.
                common.try_transfer_dicts(
                    metadata_json,
                    data,
                    [
                        "is_conflict",
                        "author",
                        "source_url",
                        "source",
                        "application_data",
                        "order",
                        "encryption_cipher_text",
                        "encryption_applied",
                        "markup_language",
                        "is_shared",
                        "share_id",
                        "conflict_original_id",
                        "master_key_id",
                        "user_data",
                        "deleted_time",
                    ],
                )
                parent_id_note_map.append(
                    (
                        metadata_json["parent_id"],
                        imf.Note(data, original_id=metadata_json["id"]),
                    )
                )
            elif type_ == ItemType.FOLDER:
                data = {
                    "title": markdown.strip(),
                    "user_created_time": common.iso_to_unix_ms(
                        metadata_json["created_time"]
                    ),
                    "user_updated_time": common.iso_to_unix_ms(
                        metadata_json["updated_time"]
                    ),
                }
                common.try_transfer_dicts(
                    metadata_json,
                    data,
                    [
                        "encryption_cipher_text",
                        "encryption_applied",
                        "is_shared",
                        "share_id",
                        "master_key_id",
                        "icon",
                        "user_data",
                        "deleted_time",
                    ],
                )
                parent_id_notebook_map.append(
                    (
                        metadata_json["parent_id"],
                        imf.Notebook(data, original_id=metadata_json["id"]),
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
                data = {
                    "title": markdown.strip(),
                    "user_created_time": common.iso_to_unix_ms(
                        metadata_json["created_time"]
                    ),
                    "user_updated_time": common.iso_to_unix_ms(
                        metadata_json["updated_time"]
                    ),
                }
                common.try_transfer_dicts(
                    metadata_json,
                    data,
                    [
                        "encryption_cipher_text",
                        "encryption_applied",
                        "is_shared",
                        "user_data",
                    ],
                )
                available_tags.append(imf.Tag(data, original_id=metadata_json["id"]))
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
                note.data["body"], resource_id_filename_map
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
        data = self.parse_data(file_or_folder)
        if data is None:
            return
        self.convert_data(*data)
