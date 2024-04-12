"""Convert notion notes to the intermediate format."""

import io
from pathlib import Path
from urllib.parse import unquote
import zipfile

import common
import intermediate_format as imf


def unzip(input_zip: Path, temp_folder: Path):
    # unzip nested zip file in notion format
    with zipfile.ZipFile(input_zip) as zip_ref:
        for nested_zip_name in zip_ref.namelist():
            with zip_ref.open(nested_zip_name) as nested_zip:
                nested_zip_filedata = io.BytesIO(nested_zip.read())
                with zipfile.ZipFile(nested_zip_filedata) as nested_zip_ref:
                    nested_zip_ref.extractall(temp_folder)


def flatten_folder(temp_folder: Path):
    # Flatten folder structure. I. e. move all files to root directory.
    # https://stackoverflow.com/a/50368037/7410886
    for item in temp_folder.iterdir():
        if item.is_dir():
            for file_ in item.iterdir():
                file_.rename(file_.parents[1] / file_.name)
            item.rmdir()


def convert(input_zip: Path, parent: imf.Notebook):
    temp_folder = common.get_temp_folder()

    unzip(input_zip, temp_folder)
    flatten_folder(temp_folder)

    for item in temp_folder.iterdir():
        if item.is_dir() or item.suffix != ".md":
            continue
        # id is appended to filename
        title, original_id = item.stem.rsplit(" ", 1)
        # first line is title, second is whitespace
        body = "\n".join(item.read_text().split("\n")[2:])

        # find links
        resources = []
        note_links = []
        for file_prefix, description, url in common.get_markdown_links(body):
            if url.startswith("http"):
                continue  # web link
            original_text = f"{file_prefix}[{description}]({url})"
            if url.endswith(".md"):
                # internal link
                _, linked_note_id = Path(unquote(url)).stem.rsplit(" ", 1)
                note_links.append(
                    imf.NoteLink(original_text, linked_note_id, description)
                )
            elif (temp_folder / url).is_file():
                # resource
                resources.append(
                    imf.Resource(temp_folder / url, original_text, description)
                )

        note_joplin = imf.Note(
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
