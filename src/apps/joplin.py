"""Convert Joplin notes to the intermediate format."""

from collections import defaultdict
from pathlib import Path
import tarfile

import common
import converter
import intermediate_format as imf


def handle_markdown_links(
    body: str, resource_id_filename_map: dict
) -> tuple[list, list]:
    note_links = []
    resources = []
    for file_prefix, description, url in common.get_markdown_links(body):
        if url.startswith("http"):
            continue  # web link
        original_text = f"{file_prefix}[{description}]({url})"
        resource_path = resource_id_filename_map.get(url[2:])
        if resource_path is None:
            # internal link
            note_links.append(imf.NoteLink(original_text, url[2:], description))
        else:
            # resource
            resources.append(imf.Resource(resource_path, original_text, description))
    return resources, note_links


class Converter(converter.BaseConverter):

    def prepare_input(self, input_: Path) -> Path | None:
        temp_folder = common.get_temp_folder()
        if input_.suffix.lower() == ".jex":
            with tarfile.open(input_) as tar_ref:
                tar_ref.extractall(temp_folder)
            return temp_folder
        self.logger.error("Unsupported format for Joplin")
        return None

    def parse_data(self, file_or_folder):
        # pylint: disable=too-many-locals
        self.root_path = self.prepare_input(file_or_folder)
        if self.root_path is None:
            return None

        parent_id_note_map = []
        parent_id_notebook_map = []
        resource_id_filename_map = {}
        available_tags = []
        note_tag_id_map = defaultdict(list)
        for file_ in self.root_path.glob("**/*.md"):
            markdown_raw = file_.read_text()
            try:
                markdown, metadata_raw = markdown_raw.rsplit("\n\n", 1)
            except ValueError:
                metadata_raw = markdown_raw
            metadata_json = {}
            for line in metadata_raw.split("\n"):
                key, value = line.split(": ", 1)
                metadata_json[key] = value

            # https://joplinapp.org/help/api/references/rest_api/#item-type-ids
            type_ = int(metadata_json["type_"])
            if type_ == 1:  # note
                title, body = markdown.split("\n", 1)
                data = {
                    "title": title.strip(),
                    "body": body.strip(),
                    "user_created_time": common.iso_to_unix_ms(
                        metadata_json["created_time"]
                    ),
                    "user_updated_time": common.iso_to_unix_ms(
                        metadata_json["updated_time"]
                    ),
                    "source_application": self.app,
                }
                common.try_transfer_dicts(
                    metadata_json,
                    data,
                    [
                        "is_conflict",
                        "latitude",
                        "longitude",
                        "altitude",
                        "author",
                        "source_url",
                        "is_todo",
                        "todo_due",
                        "todo_completed",
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
            elif type_ == 2:  # notebook
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
            elif type_ == 4:  # resource
                # TODO: metadata is lost
                filename = Path(metadata_json["id"]).with_suffix(
                    "." + metadata_json["file_extension"]
                )
                resource_id_filename_map[metadata_json["id"]] = (
                    self.root_path / "resources" / filename
                )
            elif type_ == 5:  # tag
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
            elif type_ == 6:  # note_tag
                note_tag_id_map[metadata_json["note_id"]].append(
                    metadata_json["tag_id"]
                )
            else:
                self.logger.debug(f"Ignoring note type {metadata_json['type_']}")
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
