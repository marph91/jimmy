"""Convert clipto notes to the intermediate format."""

import logging
from pathlib import Path
import zipfile

import common
import intermediate_format as imf


LOGGER = logging.getLogger("joplin_custom_importer")


def handle_markdown_links(body: str, root_folder: Path) -> tuple[list, list]:
    note_links = []
    for file_prefix, description, url in common.get_markdown_links(body):
        original_text = f"{file_prefix}[{description}]({url})"
        if url.startswith("https://dynalist.io/d"):
            # Most likely internal link. We can only try to match against the name
            # (that might me modified in the meantime).
            if (
                common.find_file_recursively(root_folder, f"{description}.txt")
                is not None
            ):
                note_links.append(imf.NoteLink(original_text, description, description))
        elif url.startswith("http"):
            continue  # web link
        else:
            # TODO: There are no resources in dynalist free plan.
            pass
    return [], note_links


def convert(zip_or_folder: Path, parent: imf.Notebook, root_folder: Path | None = None):
    if zip_or_folder.suffix.lower() == ".zip":
        temp_folder = common.get_temp_folder()
        with zipfile.ZipFile(zip_or_folder) as zip_ref:
            zip_ref.extractall(temp_folder)
        input_folder = temp_folder
    elif zip_or_folder.is_dir():
        input_folder = zip_or_folder
    else:
        LOGGER.error("Unsupported format for dynalist")
        return

    if root_folder is None:
        root_folder = input_folder

    for item in input_folder.iterdir():
        if item.is_file():
            if item.suffix != ".txt":
                # We get a zip with opml and txt. Only advantage of opml over txt is
                # the owner attribute. So just use txt, because it's simpler.
                # opml is supported by pandoc, but the import is not working properly.
                continue
            body = item.read_text()

            resources, note_links = handle_markdown_links(body, root_folder)
            tags = common.get_inline_tags(body, ["#", "@"])

            parent.child_notes.append(
                imf.Note(
                    {
                        "title": item.stem,
                        "body": body,
                        "source_application": Path(__file__).stem,
                    },
                    tags=[imf.Tag({"title": tag}, tag) for tag in tags],
                    resources=resources,
                    note_links=note_links,
                    original_id=item.stem,
                )
            )
        else:
            new_parent = imf.Notebook(
                {"title": item.name, **common.get_ctime_mtime_ms(item)}
            )
            convert(item, new_parent, root_folder=root_folder)
            parent.child_notebooks.append(new_parent)
