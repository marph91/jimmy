"""Convert Synology Note Station notes to the intermediate format."""

import copy
from dataclasses import dataclass, field
import difflib
import json
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup

import common
import converter
import intermediate_format as imf
import markdown_lib


@dataclass
class Attachment:
    """Represents a Note Station attachment."""

    filename: Path
    md5: str
    refs: list[str] = field(default_factory=list)
    titles: list[str] = field(default_factory=list)


def streamline_html(content_html: str) -> str:
    # TODO
    # pylint: disable=too-many-branches
    # another hack: make the first row of a table to the header
    soup = BeautifulSoup(content_html, "html.parser")
    for table in soup.find_all("table"):
        # Remove all divs, since they cause pandoc to fail converting the table.
        # https://stackoverflow.com/a/32064299/7410886
        for div in table.find_all("div"):
            div.unwrap()

        # another hack: Replace any newlines (<p>, <br>) with a temporary string
        # and with <br> after conversion to markdown.
        for item in table.find_all("br") + table.find_all("p"):
            text_before = "" if item.string is None else item.string
            item.string = text_before + "{TEMPORARYNEWLINE}"
            item.unwrap()

        # another hack: handle lists, i. e. replace items with "<br>- ..."
        for item in table.find_all("ul") + table.find_all("ol"):
            item.unwrap()
        for item in table.find_all("li"):
            if item.string is None:
                item.decompose()
                continue
            item.string = "{TEMPORARYNEWLINE}- " + item.string
            item.unwrap()

        for row_index, row in enumerate(table.find_all("tr")):
            for td in row.find_all("td"):
                # tables seem to be headerless always
                # make first row to header
                if row_index == 0:
                    td.name = "th"

        # remove "tbody"
        if (body := table.find("tbody")) is not None:
            body.unwrap()

    # another hack: convert iframes to simple links
    for iframe in soup.find_all("iframe"):
        iframe.name = "a"
        if not iframe.string.strip():  # link without text
            iframe.string = iframe.attrs["src"]
        iframe.attrs = {"href": iframe.attrs["src"]}

    # hack: In the original data, the attachment_id is stored in the
    # "ref" attribute. Mitigate by storing it in the "src" attribute.
    for img in soup.find_all("img"):
        if (new_src := img.attrs.get("ref")) is not None:
            img.attrs["src"] = new_src

    return str(soup)


class Converter(converter.BaseConverter):
    accepted_extensions = [".nsx"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.available_resources = []

    def find_parent_notebook(self, parent_id: str) -> imf.Notebook:
        for notebook in self.root_notebook.child_notebooks:
            if notebook.original_id == parent_id:
                return notebook
        self.logger.debug(f"Couldn't find parent notebook with id {parent_id}")
        return self.root_notebook

    def handle_markdown_links(
        self, title: str, body: str, note_id_title_map: dict, source_url: str | None
    ) -> tuple[str, imf.Resources, imf.NoteLinks]:
        resources = []
        note_links = []
        for link in markdown_lib.common.get_markdown_links(body):
            if link.is_web_link or link.is_mail_link:
                continue  # keep the original links

            if link.url.startswith("#"):
                continue  # internal link

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
            elif source_url is not None and ("/" in link.url or "?" in link.url):
                # TODO: detect relative path of a clipped website properly
                # Replace directly, since it's neither a resource nor a note link.
                new_url = urlparse(source_url)
                new_url = new_url._replace(path=link.url)

                new_link = copy.deepcopy(link)  # don't modify the original link
                new_link.url = new_url.geturl()

                body = body.replace(str(link), str(new_link))
            else:
                # resource
                # Find resource file by "ref".
                matched_resources = [
                    res for res in self.available_resources if link.url in res.refs
                ]
                if len(matched_resources) != 1:
                    self.logger.debug(
                        "Found too less or too many resources: "
                        f"{len(matched_resources)} "
                        f'(note: "{title}", original link: "{link}")'
                    )
                    continue
                resource = matched_resources[0]
                for resource_title in resource.titles:
                    resources.append(
                        imf.Resource(
                            resource.filename, str(link), link.text or resource_title
                        )
                    )
        return body, resources, note_links

    def convert_notebooks(self, input_json: dict):
        for notebook_id in input_json["notebook"]:
            notebook = json.loads(
                (self.root_path / notebook_id).read_text(encoding="utf-8")
            )

            self.root_notebook.child_notebooks.append(
                imf.Notebook(notebook["title"], original_id=notebook_id)
            )

    def map_resources_by_hash(self, note: dict) -> imf.Resources:
        resources: imf.Resources = []
        if note.get("attachment") is None:
            return resources
        for note_resource in note["attachment"].values():
            # TODO: access directly by filename (e. g. "file_<md5>")
            for file_resource in self.available_resources:
                if note_resource["md5"] == file_resource.md5:
                    if (ref := note_resource.get("ref")) is not None:
                        # The same resource can be linked multiple times.
                        file_resource.refs.append(ref)
                        file_resource.titles.append(note_resource["name"])
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

    @common.catch_all_exceptions
    def convert_note(self, note_id, note_id_title_map):
        note = json.loads((self.root_path / note_id).read_text(encoding="utf-8"))

        if note["parent_id"].rsplit("_")[-1] == "#00000000":
            self.logger.debug(f"Ignoring note in trash \"{note['title']}\"")
            return
        title = note["title"]
        self.logger.debug(f'Converting note "{title}" (ID: {note_id})')

        # resources / attachments
        resources = self.map_resources_by_hash(note)

        note_links: imf.NoteLinks = []
        if (content_html := note.get("content")) is not None:
            content_html = streamline_html(content_html)
            content_markdown = markdown_lib.common.markup_to_markdown(content_html)
            content_markdown = content_markdown.replace("{TEMPORARYNEWLINE}", "<br>")
            # note title only needed for debug message
            body, resources_referenced, note_links = self.handle_markdown_links(
                note["title"],
                content_markdown,
                note_id_title_map,
                source_url=note.get("source_url"),
            )
            resources.extend(resources_referenced)
        else:
            body = ""

        note_imf = imf.Note(
            title,
            body,
            created=common.timestamp_to_datetime(note["ctime"]),
            updated=common.timestamp_to_datetime(note["mtime"]),
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

    def convert(self, file_or_folder: Path):
        # pylint: disable=too-many-locals
        input_json = json.loads(
            (self.root_path / "config.json").read_text(encoding="utf-8")
        )

        # TODO: What is input_json["shortcut"]?
        # TODO: Are nested notebooks possible?

        self.convert_notebooks(input_json)

        # dirty hack: Only option to map the files from file system
        # to the note content is by MD5 hash.
        for item in sorted(self.root_path.iterdir()):
            if item.is_file() and item.stem.startswith("file_"):
                if item.stem.startswith("file_thumb"):
                    continue  # ignore thumbnails
                # Don't use the actual hash: hashlib.md5(item.read_bytes()).hexdigest()
                # It can change. So we need to take the hash from the filename.
                self.available_resources.append(
                    Attachment(item, item.stem.split("_")[-1])
                )

        # for internal links, we need to store the note titles
        note_id_title_map = {}
        for note_id in input_json["note"]:
            note = json.loads((self.root_path / note_id).read_text(encoding="utf-8"))
            note_id_title_map[note_id] = note["title"]

        for note_id in input_json["note"]:
            self.convert_note(note_id, note_id_title_map)
