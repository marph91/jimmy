import argparse
from datetime import datetime
from enum import Enum
from functools import partial
import importlib
from pathlib import Path
import pkgutil
import shutil

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
    parser.add_argument("--api-token", required=True, help="Joplin API token.")
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

    # import to Joplin
    api = Api(token=args.api_token)
    importer = JoplinImporter(api)
    importer.import_tags(tags)
    importer.import_notebook(root_tree)


if __name__ == "__main__":
    main()
