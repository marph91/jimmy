"""Convert Synology Note Station notes to the intermediate format."""

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re

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
    accepted_extensions = [".nsx", ".zip"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.available_resources = []

    def prepare_input(self, input_: Path) -> Path:
        return common.extract_zip(input_)

    def find_parent_notebook(self, parent_id: str) -> imf.Notebook:
        for notebook in self.root_notebook.child_notebooks:
            if notebook.original_id == parent_id:
                return notebook
        self.logger.debug(f"Couldn't find parent notebook with id {parent_id}")
        return self.root_notebook

    def handle_markdown_links(self, title: str, body: str) -> tuple[list, list]:
        resources = []
        for link in common.get_markdown_links(body):
            if link.is_web_link or link.is_mail_link:
                continue  # keep the original links
            # resource
            # Find resource file by "ref".
            matched_resources = [
                res for res in self.available_resources if res.ref == link.url
            ]
            if len(matched_resources) != 1:
                self.logger.debug(
                    f"Found too less or too many resources: {len(matched_resources)} "
                    f'(note: "{title}", original link: "{link}")'
                )
                continue
            resource = matched_resources[0]
            resources.append(
                imf.Resource(resource.filename, str(link), link.text or resource.title)
            )
        return resources, []

    def convert_notebooks(self, input_json: dict):
        for notebook_id in input_json["notebook"]:
            notebook = json.loads(
                (self.root_path / notebook_id).read_text(encoding="utf-8")
            )

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
        resources: list[imf.Resource] = []
        if note.get("attachment") is None:
            return resources
        for note_resource in note["attachment"].values():
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
        input_json = json.loads(
            (self.root_path / "config.json").read_text(encoding="utf-8")
        )

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
            try:
                note = json.loads(
                    (self.root_path / note_id).read_text(encoding="utf-8")
                )

                # resources / attachments
                resources = self.map_resources_by_hash(note)

                data = {
                    "title": note["title"],
                    "user_created_time": note["ctime"],
                    "user_updated_time": note["mtime"],
                    "source_application": self.format,
                }
                if (content_html := note.get("content")) is not None:
                    # hack: In the original data, the attachment_id is stored in the
                    # "ref" attribute. Mitigate by storing it in the "src" attribute.
                    content_html = re.sub("<img.*?ref=", "<img src=", content_html)
                    content_markdown = common.html_text_to_markdown(content_html)
                    # note title only needed for debug message
                    resources_referenced, _ = self.handle_markdown_links(
                        note["title"], content_markdown
                    )
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
            except Exception as exc:  # pylint: disable=broad-except
                self.logger.warning(f"Failed to convert note \"{note['title']}\"")
                # https://stackoverflow.com/a/52466005/7410886
                self.logger.debug(exc, exc_info=True)
