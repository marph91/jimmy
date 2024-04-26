"""Convert Synology Note Station notes to the intermediate format."""

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import zipfile

import common
import converter
import intermediate_format as imf


@dataclass
class Attachment:
    """Represents a Note Station attachment."""

    filename: Path
    md5: str
    ref: str | None = None
    title: str | None = None


class Converter(converter.BaseConverter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.available_resources = []

    def prepare_input(self, input_: Path) -> Path | None:
        if input_.suffix.lower() in (".nsx", ".zip"):
            temp_folder = common.get_temp_folder()
            with zipfile.ZipFile(input_) as zip_ref:
                zip_ref.extractall(temp_folder)
            return temp_folder
        if input_.is_dir():
            return input_
        self.logger.error(f"Unsupported format for {self.app}")
        return None

    def find_parent_notebook(self, parent_id) -> imf.Notebook:
        for notebook in self.root_notebook.child_notebooks:
            if notebook.original_id == parent_id:
                return notebook
        self.logger.debug(f"Couldn't find parent notebook with id {parent_id}")
        return self.root_notebook

    def handle_markdown_links(self, body: str) -> tuple[list, list]:
        resources = []
        for file_prefix, description, url in common.get_markdown_links(body):
            if url.startswith("http") or url.startswith("mailto:"):
                continue  # web link / mail
            original_text = f"{file_prefix}[{description}]({url})"
            # resource
            # Find resource file by "ref".
            matched_resources = [
                res for res in self.available_resources if res.ref == url
            ]
            if len(matched_resources) != 1:
                self.logger.debug(
                    "Found too less or too many resource: {len(matched_resources)}"
                )
                continue
            resource = matched_resources[0]
            resources.append(
                imf.Resource(
                    resource.filename, original_text, description or resource.title
                )
            )
        return resources, []

    def convert_notebooks(self, input_json: dict):
        for notebook_id in input_json["notebook"]:
            notebook = json.loads((self.root_path / notebook_id).read_text())

            self.root_notebook.child_notebooks.append(
                imf.Notebook(
                    {
                        "title": notebook["title"],
                        "user_created_time": notebook["ctime"],
                        "user_updated_time": notebook["mtime"],
                    },
                    original_id=notebook_id,
                )
            )

    def map_resources_by_hash(self, note: dict) -> list[imf.Resource]:
        resources = []
        for note_resource in note.get("attachment", {}).values():
            for file_resource in self.available_resources:
                if note_resource["md5"] == file_resource.md5:
                    if (ref := note_resource.get("ref")) is not None:
                        file_resource.ref = ref
                        file_resource.title = note_resource["name"]
                    else:
                        # The attachment is not referenced. Add it here.
                        # Referenced attachments are added later.
                        resources.append(
                            imf.Resource(
                                file_resource.filename, title=note_resource["name"]
                            )
                        )
                    break
        return resources

    def convert(self, file_or_folder: Path):
        self.root_path = self.prepare_input(file_or_folder)
        if self.root_path is None:
            return
        input_json = json.loads((self.root_path / "config.json").read_text())

        # TODO: What is input_json["shortcut"]?
        # TODO: Are nested notebooks possible?

        self.convert_notebooks(input_json)

        # dirty hack: Only option to map the files from file system
        # to the note content is by MD5 hash.
        for item in self.root_path.iterdir():
            if item.is_file() and item.stem.startswith("file_"):
                self.available_resources.append(
                    Attachment(item, hashlib.md5(item.read_bytes()).hexdigest())
                )

        for note_id in input_json["note"]:
            note = json.loads((self.root_path / note_id).read_text())

            # resources / attachments
            resources = self.map_resources_by_hash(note)

            data = {
                "title": note["title"],
                "user_created_time": note["ctime"],
                "user_updated_time": note["mtime"],
                "source_application": self.app,
            }
            if (content_html := note.get("content")) is not None:
                # dirty hack: In the original data, the attachment_id is stored in the
                # "ref" attribute. Mitigate by storing it in the "src" attribute.
                content_html = re.sub("<img.*?ref=", "<img src=", content_html)
                content_markdown = common.html_text_to_markdown(content_html)
                resources_referenced, _ = self.handle_markdown_links(content_markdown)
                resources.extend(resources_referenced)
                data["body"] = content_markdown

            common.try_transfer_dicts(
                note, data, ["latitude", "longitude", "source_url"]
            )

            parent_notebook = self.find_parent_notebook(note["parent_id"])
            parent_notebook.child_notes.append(
                imf.Note(
                    data,
                    tags=[imf.Tag({"title": tag}) for tag in note.get("tag", [])],
                    resources=resources,
                    original_id=note_id,
                )
            )
