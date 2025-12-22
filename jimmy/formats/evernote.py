"""
Convert Evernote notes to the intermediate format.
Specification: https://evernote.com/blog/how-evernotes-xml-export-format-works
"""

import base64
import collections
import hashlib
from pathlib import Path
from urllib.parse import unquote
import uuid
import xml.etree.ElementTree as ET  # noqa: N817

from jimmy import common, converter, intermediate_format as imf
import jimmy.md_lib.evernote
import jimmy.md_lib.links


class Converter(converter.BaseConverter):
    def __init__(self, config):
        super().__init__(config)
        self.password = config.password
        # we need a resource folder to avoid writing files to the source folder
        self.resource_folder = common.get_temp_folder()
        self.note_id_title_map = {}

    def handle_markdown_links(self, body: str) -> tuple[imf.Resources, imf.NoteLinks]:
        # resources and other links are mostly handled already
        note_links = []
        resources = []
        for link in jimmy.md_lib.links.get_markdown_links(body):
            if not link.url.startswith("https://www.evernote.com/shard") and (
                link.is_web_link or link.is_mail_link
            ):
                continue  # keep the original links

            if link.url.startswith("evernote://") or link.url.startswith(
                "https://www.evernote.com/shard"
            ):
                # internal link
                best_match_id = common.get_best_match(link.text, self.note_id_title_map)
                if best_match_id is not None:
                    note_links.append(imf.NoteLink(str(link), best_match_id, link.text))
            elif link.url.startswith("data:image/") and "base64" in link.url:
                # inline resource
                base64_data = link.url.split("base64,", 1)[1]  # TODO: make more robust
                temp_filename = self.resource_folder / (
                    common.unique_title() if link.text in [None, ""] else link.text
                )
                temp_filename = common.write_base64(temp_filename, base64_data)
                resources.append(imf.Resource(temp_filename, str(link), link.text))
            elif link.url.startswith("data:image/svg+xml,"):
                svg_data = unquote(link.url[len("data:image/svg+xml,") :])
                temp_filename = self.resource_folder / (
                    common.unique_title() + ".svg" if link.text in [None, ""] else link.text
                )
                temp_filename = common.get_unique_path(temp_filename, svg_data)
                temp_filename.write_text(svg_data)
                resources.append(imf.Resource(temp_filename, str(link), link.text))
        return resources, note_links

    def link_notes_by_title(self):
        for note in self.root_notebook.get_all_child_notes():
            resources, note_links = self.handle_markdown_links(note.body)
            note.resources.extend(resources)
            note.note_links.extend(note_links)

    @common.catch_all_exceptions
    def convert_note(self, note, parent_notebook: imf.Notebook):
        title = note.find("title")
        title = common.unique_title() if title is None or title.text is None else title.text.strip()
        self.logger.debug(f'Converting note "{title}"')
        note_imf = imf.Note(
            title,
            # The ids are not exported. We can only try to match
            # against the title later. A unique ID is still required.
            original_id=str(uuid.uuid4()),
            source_application=self.format,
        )
        self.note_id_title_map[note_imf.original_id] = note_imf.title

        hashes: list[str] = []
        tasks = collections.defaultdict(list)
        for note_element in note:
            match note_element.tag:
                case "title":
                    pass  # handled already
                case "content":
                    if note_element.text:
                        parser = ET.XMLParser(
                            target=jimmy.md_lib.evernote.EnexToMarkdown(self.password)
                        )
                        try:
                            parser.feed(note_element.text.strip())
                        except ET.ParseError as exc:
                            self.logger.error("Failed to parse note")
                            self.logger.debug(exc, exc_info=True)
                            continue
                        # assume that this is done always before "resource"
                        body, hashes = parser.close()  # type: ignore[assignment]
                        note_imf.body = body  # type: ignore[assignment]
                case "created" | "updated":
                    if note_element.text is None:
                        continue
                    try:
                        setattr(
                            note_imf,
                            note_element.tag,
                            common.iso_to_datetime(note_element.text),
                        )
                    except ValueError:
                        self.logger.debug("couldn't parse date")
                case "resource":
                    # Use the original filename if possible.
                    resource_title = note_element.find("./resource-attributes/file-name")
                    resource_data = note_element.find("data")
                    if resource_data is None or not resource_data.text:
                        self.logger.debug("Skip empty resource")
                        continue
                    if (encoding := resource_data.get("encoding")) != "base64":
                        self.logger.debug(f"Unsupported encoding: {encoding}")
                    temp_filename = self.resource_folder / (
                        common.unique_title()
                        if resource_title is None or not isinstance(resource_title.text, str)
                        else common.safe_path(resource_title.text)
                    )
                    resource_data_decoded = base64.b64decode(resource_data.text)
                    md5_hash = hashlib.md5(resource_data_decoded).hexdigest()
                    temp_filename = common.write_base64(temp_filename, resource_data.text)
                    resource_title = (
                        resource_title if resource_title is None else resource_title.text
                    )
                    if md5_hash in hashes:
                        resource_md = f"![]({md5_hash})"
                        note_imf.resources.append(
                            imf.Resource(temp_filename, resource_md, resource_title)
                        )
                    else:
                        note_imf.resources.append(imf.Resource(temp_filename, None, resource_title))
                case "tag":
                    if isinstance(note_element.text, str):
                        note_imf.tags.append(imf.Tag(note_element.text))
                case "task":
                    status_element = note_element.find("taskStatus")
                    bullet = (
                        "- [ ] "
                        if status_element is not None and status_element.text == "open"
                        else "- [x] "
                    )
                    task_group_element = note_element.find("taskGroupNoteLevelID")
                    if task_group_element is not None and (
                        task_group_id := task_group_element.text
                    ) not in [None, ""]:
                        title_element = note_element.find("title")
                        if (
                            title_element is None
                            or not isinstance(title_element.text, str)
                            or title_element.text == ""
                        ):
                            continue
                        weight_element = note_element.find("sortWeight")
                        weight = (
                            "a"
                            if weight_element is None or not isinstance(weight_element.text, str)
                            else weight_element.text
                        )
                        tasks[task_group_id].append([weight, f"{bullet}{title_element.text}\n"])
                case "note-attributes":
                    for attr in note_element:
                        match attr.tag:
                            case "author" | "latitude" | "longitude" | "altitude":
                                setattr(note_imf, note_element.tag, attr.text)
                            case (
                                "reminder-order"
                                | "reminder-done-time"
                                | "reminder-time"
                                | "source"
                                | "source-application"
                                | "source-url"
                            ):
                                pass  # TODO
                            case _:
                                self.logger.debug(f"ignoring attr {attr.tag}")
                case _:
                    self.logger.debug(f"ignoring tag {note_element.tag}")
        # replace tasks
        for group_id, tasks_md in tasks.items():
            # tasks_md: [list_index, markdown task]
            tasks_sorted_md = "".join([t[1] for t in sorted(tasks_md, key=lambda t: t[0])])
            note_imf.body = note_imf.body.replace(f"tasklist://{group_id}", "\n" + tasks_sorted_md)
        parent_notebook.child_notes.append(note_imf)

    @common.catch_all_exceptions
    def convert_file(self, file_or_folder: Path, parent_notebook: imf.Notebook):
        self.logger.debug(f'Converting note "{file_or_folder.name}"')
        # We are only interested in complete notes.
        for _, elem in ET.iterparse(file_or_folder, events=("end",)):
            if elem.tag == "note":
                self.convert_note(elem, parent_notebook)

    def convert(self, file_or_folder: Path):
        if file_or_folder.is_file():
            self.convert_file(file_or_folder, self.root_notebook)
        else:
            for file_ in sorted(file_or_folder.glob("*.enex")):
                parent_notebook = imf.Notebook(file_.stem)
                self.root_notebook.child_notebooks.append(parent_notebook)
                self.convert_file(file_, parent_notebook)

        # second pass: match note links by name
        self.link_notes_by_title()

        # Don't export empty notebooks
        self.remove_empty_notebooks()
