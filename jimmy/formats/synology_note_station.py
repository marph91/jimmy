"""Convert Synology Note Station notes to the intermediate format."""

import copy
import dataclasses
import json
from pathlib import Path
from urllib.parse import urlparse

from jimmy import common, converter, intermediate_format as imf
import jimmy.md_lib.convert
import jimmy.md_lib.html_filter
import jimmy.md_lib.links


@dataclasses.dataclass
class Attachment:
    """Represents a Note Station attachment."""

    filename: Path
    md5: str
    refs: list[str] = dataclasses.field(default_factory=list)
    titles: list[str] = dataclasses.field(default_factory=list)


class Converter(converter.BaseConverter):
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
        for link in jimmy.md_lib.links.get_markdown_links(body):
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

                best_match_id = common.get_best_match(link.text, note_id_title_map)
                if best_match_id is not None:
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
                        imf.Resource(resource.filename, str(link), link.text or resource_title)
                    )
        return body, resources, note_links

    def convert_notebooks(self, input_json: dict):
        for notebook_id in input_json["notebook"]:
            notebook = json.loads((self.root_path / notebook_id).read_text(encoding="utf-8"))

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
                            imf.Resource(file_resource.filename, title=note_resource["name"])
                        )
                    break
        return resources

    @common.catch_all_exceptions
    def convert_note(self, note_id, note_id_title_map):
        note = json.loads((self.root_path / note_id).read_text(encoding="utf-8"))

        if note["parent_id"].rsplit("_")[-1] == "#00000000":
            self.logger.debug(f'Ignoring note in trash "{note["title"]}"')
            return
        title = note["title"]
        self.logger.debug(f'Converting note "{title}" (ID: "{note_id}")')

        # resources / attachments
        resources = self.map_resources_by_hash(note)

        note_links: imf.NoteLinks = []
        if (content_html := note.get("content")) is not None:
            content_markdown = self.pandoc.markup_to_markdown(
                content_html,
                custom_filter=[
                    jimmy.md_lib.html_filter.synology_note_station_fix_checklists,
                    jimmy.md_lib.html_filter.synology_note_station_fix_img_src,
                ],
            )
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
        input_json = json.loads((self.root_path / "config.json").read_text(encoding="utf-8"))
        if "note" not in input_json:
            self.logger.error('"note" not found. Is this really a Synology Note Station export?')
            return

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
                self.available_resources.append(Attachment(item, item.stem.split("_")[-1]))

        # for internal links, we need to store the note titles
        note_id_title_map = {}
        for note_id in input_json["note"]:
            note = json.loads((self.root_path / note_id).read_text(encoding="utf-8"))
            note_id_title_map[note_id] = note["title"]

        for note_id in input_json["note"]:
            self.convert_note(note_id, note_id_title_map)
