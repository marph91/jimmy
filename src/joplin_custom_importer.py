import argparse
from datetime import datetime
import importlib
from pathlib import Path
import pkgutil

import pypandoc

import api_helper
import apps
from common import JoplinImporter, Note, Notebook


# https://stackoverflow.com/a/287944/7410886
COLOR_SUCCESS = "\033[92m"
COLOR_FAIL = "\033[91m"
COLOR_END = "\033[0m"


def convert_folder(folder: Path, root):
    """Default conversion function for folders."""
    for item in folder.iterdir():
        if item.is_file():
            try:
                root, _ = convert_file(item, root)
                print(f"- {COLOR_SUCCESS}{item.name}{COLOR_END}")
            except Exception as exc:  # pylint: disable=broad-except
                print(f"- {COLOR_FAIL}{item.name}{COLOR_END}: {str(exc).strip()[:120]}")
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
    parser.add_argument(
        "--dry-run", action="store_true", help="Don't connect to the Joplin API."
    )
    args = parser.parse_args()

    if not args.dry_run:
        # create the connection to Joplin first to fail fast in case of a problem
        api = api_helper.get_api()

    # root notebook
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    root = Notebook({"title": f"{now} - Import"})
    # Convert the input data to an intermediate representation
    # that can be used by the importer later.
    # Try to use an app specific converter. If there is none,
    # fall back to the default converter.
    try:
        module = importlib.import_module(f"apps.{args.app}")
        conversion_function = module.convert
    except ModuleNotFoundError:
        conversion_function = convert_file if args.input.is_file() else convert_folder
    root_tree, tags = conversion_function(args.input, root)

    if not args.dry_run:
        # import to Joplin
        importer = JoplinImporter(api)
        importer.import_tags(tags)
        importer.import_notebook(root_tree)


if __name__ == "__main__":
    main()
