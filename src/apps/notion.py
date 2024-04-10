"""Convert notion notes to the intermediate format."""

import io
from pathlib import Path
import re
import tempfile
import time
import zipfile

import common
from intermediate_format import Note, Notebook, NoteLink, Resource


def convert(input_zip: Path, parent: Notebook):
    # TODO: note links and attachments
    temp_folder = Path(tempfile.gettempdir()) / f"joplin_export_{int(time.time())}"

    # unzip nested zip file
    with zipfile.ZipFile(input_zip) as zip_ref:
        for nested_zip_name in zip_ref.namelist():
            with zip_ref.open(nested_zip_name) as nested_zip:
                nested_zip_filedata = io.BytesIO(nested_zip.read())
                with zipfile.ZipFile(nested_zip_filedata) as nested_zip_ref:
                    nested_zip_ref.extractall(temp_folder)

    # Flatten folder structure. I. e. move all files to root directory.
    # https://stackoverflow.com/a/50368037/7410886
    for item in temp_folder.iterdir():
        if item.is_dir():
            for file_ in item.iterdir():
                file_.rename(file_.parents[1] / file_.name)
            item.rmdir()

    for item in temp_folder.iterdir():
        if item.is_dir():
            continue
        if item.suffix == ".md":
            # id is appended to filename
            title, original_id = item.stem.rsplit(" ", 1)
            # first line is title, second is whitespace
            body = "\n".join(item.read_text().split("\n")[2:])

            # find links
            resources = []
            note_links = []
            for description, url in common.get_markdown_links(body):
                if url.startswith("http"):
                    continue  # web link
                elif url.endswith(".md"):
                    # internal link
                    _, linked_note_id = Path(url).stem.rsplit("%20", 1)
                    note_links.append(
                        NoteLink(f"[{description}]({url})", linked_note_id, description)
                    )
                elif (temp_folder / url).is_file():
                    # resource
                    resources.append(
                        Resource(
                            temp_folder / url, f"[{description}]({url})", description
                        )
                    )

            note_joplin = Note(
                {
                    "title": title,
                    "body": body,
                    "source_application": Path(__file__).stem,
                },
                original_id=original_id,
                resources=resources,
                note_links=note_links,
            )
            parent.child_notes.append(note_joplin)
