"""Convert obsidian notes to the intermediate format."""

import logging
from pathlib import Path
from urllib.parse import unquote

import common
import intermediate_format as imf


LOGGER = logging.getLogger("joplin_custom_importer")


def find_obsidian_resource(root_folder, url) -> Path | None:
    # Resources can be located anywhere?!
    potential_matches = list(root_folder.glob(f"**/{url}"))
    if not potential_matches:
        LOGGER.debug(f"Couldn't find match for resource {url}")
        return None
    if len(potential_matches) > 1:
        LOGGER.debug(f"Found too many matches for resource {url}")
    return potential_matches[0]


def handle_markdown_links(body: str, root_folder: Path) -> tuple[list, list]:
    # markdown links
    note_links = []
    resources = []
    for file_prefix, description, url in common.get_markdown_links(body):
        if url.startswith("http"):
            continue  # web link
        original_text = f"{file_prefix}[{description}]({url})"
        if url.endswith(".md"):
            # internal link
            linked_note_id = Path(unquote(url)).stem
            note_links.append(imf.NoteLink(original_text, linked_note_id, description))
        else:
            # resource
            resource_path = find_obsidian_resource(root_folder, url)
            if resource_path is None:
                continue
            resources.append(imf.Resource(resource_path, original_text, description))
    return resources, note_links


def handle_wikilink_links(body: str, root_folder: Path) -> tuple[list, list]:
    # https://help.obsidian.md/Linking+notes+and+files/Internal+links
    # wikilink links
    note_links = []
    resources = []
    for file_prefix, url, description in common.get_wikilink_links(body):
        alias = "" if description.strip() == "" else f"|{description}"
        original_text = f"{file_prefix}[[{url}{alias}]]"
        if file_prefix:
            resource_path = find_obsidian_resource(root_folder, url)
            if resource_path is None:
                continue
            resources.append(
                imf.Resource(resource_path, original_text, description or url)
            )
        else:
            # internal link
            note_links.append(imf.NoteLink(original_text, url, description or url))
    return resources, note_links


def convert(folder: Path, parent: imf.Notebook, root_folder: Path | None = None):
    if root_folder is None:
        root_folder = folder

    for item in folder.iterdir():
        if item.is_dir() and item.name == ".obsidian":
            continue  # ignore the internal obsidian folder
        if item.is_file():
            if item.suffix != ".md":
                continue
            note_links = []
            resources = []
            body = item.read_text()

            wikilink_resources, wikilink_note_links = handle_wikilink_links(
                body, root_folder
            )
            markdown_resources, markdown_note_links = handle_markdown_links(
                body, root_folder
            )
            resources.extend(wikilink_resources + markdown_resources)
            note_links.extend(wikilink_note_links + markdown_note_links)

            parent.child_notes.append(
                imf.Note(
                    {
                        "title": item.stem,
                        "body": body,
                        "source_application": Path(__file__).stem,
                    },
                    original_id=item.stem,
                    resources=resources,
                    note_links=note_links,
                )
            )
        else:
            new_parent = imf.Notebook(
                {
                    "title": item.name,
                    "user_created_time": item.stat().st_ctime * 1000,
                    "user_updated_time": item.stat().st_mtime * 1000,
                }
            )
            convert(item, new_parent, root_folder=root_folder)
            parent.child_notebooks.append(new_parent)
