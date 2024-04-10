"""Convert obsidian notes to the intermediate format."""

import logging
from pathlib import Path
import re
from typing import Optional

import common
from intermediate_format import Note, Notebook, NoteLink, Resource


LOGGER = logging.getLogger("joplin_custom_importer")


def convert(folder: Path, parent: Notebook, root_folder: Optional[Path] = None):
    if root_folder is None:
        root_folder = folder

    for item in folder.iterdir():
        note_links = []
        resources = []
        if item.is_file():
            if item.suffix == ".md":
                body = item.read_text()

                # https://help.obsidian.md/Linking+notes+and+files/Internal+links
                # TODO: markdown links
                for file_prefix, url, description in common.get_wikilink_links(body):
                    alias = "" if description.strip() == "" else f"|{description}"
                    original_text = f"{file_prefix}[[{url}{alias}]]"
                    if file_prefix:
                        # Resources can be located anywhere?!
                        potential_matches = list(root_folder.glob(f"**/{url}"))
                        if not potential_matches:
                            LOGGER.debug(f"Couldn't find match for resource {url}")
                            continue
                        resources.append(
                            # TODO: is image and add ! in markdown -> ![]()
                            Resource(
                                potential_matches[0], original_text, description or url
                            )
                        )
                    else:
                        # internal link
                        note_links.append(
                            NoteLink(original_text, url, description or url)
                        )

                parent.child_notes.append(
                    Note(
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
            new_parent = Notebook(
                {
                    "title": item.name,
                    "user_created_time": item.stat().st_ctime * 1000,
                    "user_updated_time": item.stat().st_mtime * 1000,
                }
            )
            convert(item, new_parent, root_folder=root_folder)
            parent.child_notebooks.append(new_parent)
