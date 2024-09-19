"""Convert Synology Note Station notes to the intermediate format."""

from dataclasses import dataclass
import datetime as dt
import difflib
import hashlib
import json
from pathlib import Path
import re

from bs4 import BeautifulSoup

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


def streamline_html(content_html: str) -> str:
    # hack: In the original data, the attachment_id is stored in the
    # "ref" attribute. Mitigate by storing it in the "src" attribute.
    content_html = re.sub("<img.*?ref=", "<img src=", content_html)

    # another hack: make the first row of a table to the header
    soup = BeautifulSoup(content_html, "html.parser")
    for table in soup.find_all("table"):
        for row_index, row in enumerate(table.find_all("tr")):
            for td in row.find_all("td"):
                # tables seem to be headerless always
                # make first row to header
                if row_index == 0:
                    td.name = "th"
        # remove "tbody"
        body = table.find("tbody")
        body.unwrap()

    return str(soup)


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

    def handle_markdown_links(
        self, title: str, body: str, note_id_title_map: dict
    ) -> tuple[list, list]:
        resources = []
        note_links = []
        for link in common.get_markdown_links(body):
            if link.is_web_link or link.is_mail_link:
                continue  # keep the original links

            if link.url.startswith("notestation://"):
                # internal link
                # Linked note ID doesn't correspond to the real note ID. For example:
                # - filename: note_VW50aXRsZWQgTm90ZTE2MTM0MDQ5NDQ2NzY=
                # - link: notestation://remote/self/1026_1547KOMP551EN92DDB4FIOFUNK
                # TODO: Is there a connection between the ID's?
                # _, linked_note_id = link.url.rsplit("/", 1)

                # try to map by title similarity
                def get_match_ratio(id_, link_text=link.text):
                    return difflib.SequenceMatcher(
                        None, link_text, note_id_title_map[id_]
                    ).ratio()

                best_match_id = max(note_id_title_map, key=get_match_ratio)
                note_links.append(imf.NoteLink(str(link), best_match_id, link.text))
            else:
                # resource
                # Find resource file by "ref".
                matched_resources = [
                    res for res in self.available_resources if res.ref == link.url
                ]
                if len(matched_resources) != 1:
                    self.logger.debug(
                        "Found too less or too many resources: "
                        f"{len(matched_resources)} "
                        f'(note: "{title}", original link: "{link}")'
                    )
                    continue
                resource = matched_resources[0]
                resources.append(
                    imf.Resource(
                        resource.filename, str(link), link.text or resource.title
                    )
                )
        return resources, note_links

    def convert_notebooks(self, input_json: dict):
        for notebook_id in input_json["notebook"]:
            notebook = json.loads(
                (self.root_path / notebook_id).read_text(encoding="utf-8")
            )

            self.root_notebook.child_notebooks.append(
                imf.Notebook(notebook["title"], original_id=notebook_id)
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
        # pylint: disable=too-many-locals

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

        # for internal links, we need to store the note titles
        note_id_title_map = {}
        for note_id in input_json["note"]:
            note = json.loads((self.root_path / note_id).read_text(encoding="utf-8"))
            note_id_title_map[note_id] = note["title"]

        for note_id in input_json["note"]:
            try:
                note = json.loads(
                    (self.root_path / note_id).read_text(encoding="utf-8")
                )

                if note["parent_id"].rsplit("_")[-1] == "#00000000":
                    self.logger.debug(f"Ignoring note in trash \"{note['title']}\"")
                    continue

                # resources / attachments
                resources = self.map_resources_by_hash(note)

                note_links: list[imf.NoteLink] = []
                if (content_html := note.get("content")) is not None:
                    content_html = streamline_html(content_html)
                    content_markdown = common.markup_to_markdown(content_html)
                    # note title only needed for debug message
                    resources_referenced, note_links = self.handle_markdown_links(
                        note["title"], content_markdown, note_id_title_map
                    )
                    resources.extend(resources_referenced)
                    body = content_markdown
                else:
                    body = ""

                note_imf = imf.Note(
                    note["title"],
                    body,
                    created=dt.datetime.utcfromtimestamp(note["ctime"]),
                    updated=dt.datetime.utcfromtimestamp(note["mtime"]),
                    source_application=self.format,
                    tags=[imf.Tag(tag) for tag in note.get("tag", [])],
                    resources=resources,
                    note_links=note_links,
                    original_id=note_id,
                )
                if (latitude := note.get("latitude")) is not None:
                    note_imf.latitude = latitude
                if (longitude := note.get("longitude")) is not None:
                    note_imf.longitude = longitude

                parent_notebook = self.find_parent_notebook(note["parent_id"])
                parent_notebook.child_notes.append(note_imf)
            except Exception as exc:  # pylint: disable=broad-except
                self.logger.warning(f"Failed to convert note \"{note['title']}\"")
                # https://stackoverflow.com/a/52466005/7410886
                self.logger.debug(exc, exc_info=True)
