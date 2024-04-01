import argparse
from datetime import datetime
from enum import Enum
from functools import partial
import importlib
from pathlib import Path
import pkgutil
import shutil
import tempfile

from asciidoc3 import asciidoc3api
from joppy.api import Api
import pypandoc

import apps
from common import *


def convert_folder(folder: Path, root):
    """Default conversion function for folders."""
    for item in folder.iterdir():
        if item.is_file():
            try:
                convert_file(item, root)
                print(f"{item.name}: success")
            except Exception as exc:
                print(f"{item.name}: {str(exc).strip()}")
        else:
            new_root, _ = convert_folder(item, Notebook({"title": item.name}))
            root.child_notebooks.append(new_root)
    return root, []


def convert_file(file_: Path, root):
    """Default conversion function for files. Uses pandoc directly."""
    if file_.suffix == ".adoc":
        # Convert asciidoc separately, since reading is not supported by pandc (yet).
        with tempfile.NamedTemporaryFile(suffix=".docbook") as docbook_file:
            # https://gitlab.com/asciidoc3/asciidoc3/-/issues/5#note_752781763
            asciidoc3_api = asciidoc3api.AsciiDoc3API(Path(asciidoc3api.__file__))
            asciidoc3_api.execute(str(file_), docbook_file.name, backend="docbook")
            note_body = pypandoc.convert_file(docbook_file.name, "commonmark_x")
            root.child_notes.append(Note({"title": file_.stem, "body": note_body}))
    else:
        # markdown output formats: https://pandoc.org/chunkedhtml-demo/8.22-markdown-variants.html
        # Joplin follows CommonMark: https://joplinapp.org/help/apps/markdown
        note_body = pypandoc.convert_file(file_, "commonmark_x")
        root.child_notes.append(Note({"title": file_.stem, "body": note_body}))
    return root, []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="The input file or folder.")
    # specific apps that need a special handling
    parser.add_argument(
        "--app",
        choices=[module.name for module in pkgutil.iter_modules(apps.__path__)],
        help="The source application.",
    )
    group_api = parser.add_mutually_exclusive_group(required=True)
    group_api.add_argument("--api-token", help="Joplin API token.")
    group_api.add_argument(
        "--dry-run", action="store_true", help="Don't connect to the Joplin API."
    )
    args = parser.parse_args()

    # root notebook
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    root = Notebook({"title": f"{now} - Import"})
    # convert the input data to an intermediate representation that can be used by the importer later
    # try to use an app specific converter
    # if there is none, fall back to the default converter
    try:
        module = importlib.import_module(f"apps.{args.app}")
        conversion_function = module.convert
    except ModuleNotFoundError:
        conversion_function = convert_file if args.input.is_file() else convert_folder
    root_tree, tags = conversion_function(args.input, root)

    if not args.dry_run:
        # import to Joplin
        api = Api(token=args.api_token)
        importer = JoplinImporter(api)
        importer.import_tags(tags)
        importer.import_notebook(root_tree)


if __name__ == "__main__":
    main()
