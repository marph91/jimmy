"""Importer for many (note) formats to Joplin."""

import argparse
from datetime import datetime
import importlib
import logging
from pathlib import Path
import pkgutil
from typing import Tuple

import pypandoc

import api_helper
import apps
import importer
from intermediate_format import Note, Notebook


LOGGER = logging.getLogger("joplin_custom_importer")


def setup_logging(log_to_file):
    # mute other logger
    logging.getLogger("pypandoc").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("joppy").setLevel(logging.WARNING)

    # setup the root logger, but don't propagate. We will log using our own
    # log handler. See: https://stackoverflow.com/a/71365918/7410886
    logging.basicConfig(level=logging.DEBUG)
    LOGGER.propagate = False

    if log_to_file:
        # log to file
        file_handler_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)-5.5s]  %(message)s"
        )
        file_handler = logging.FileHandler("joplin_custom_importer.log", mode="w")
        file_handler.setFormatter(file_handler_formatter)
        file_handler.setLevel(logging.DEBUG)
        LOGGER.addHandler(file_handler)

    # log to stdout
    console_handler_formatter = logging.Formatter("[%(levelname)-5.5s] %(message)s")
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_handler_formatter)
    console_handler.setLevel(logging.INFO)
    LOGGER.addHandler(console_handler)


def convert_folder(folder: Path, parent: Notebook) -> Tuple[Notebook, list]:
    """Default conversion function for folders."""
    for item in folder.iterdir():
        if item.is_file():
            try:
                convert_file(item, parent)
                LOGGER.debug(f"ok   {item.name}")
            except Exception as exc:  # pylint: disable=broad-except
                LOGGER.debug(f"fail {item.name}: {str(exc).strip()[:120]}")
        else:
            new_parent = Notebook(
                {
                    "title": item.name,
                    "user_created_time": item.stat().st_ctime * 1000,
                    "user_updated_time": item.stat().st_mtime * 1000,
                }
            )
            convert_folder(item, new_parent)
            parent.child_notebooks.append(new_parent)


def convert_file(file_: Path, parent: Notebook) -> Tuple[Notebook, list]:
    """Default conversion function for files. Uses pandoc directly."""
    if file_.suffix in (".md", ".txt"):
        note_body = file_.read_text()
    else:
        # markdown output formats: https://pandoc.org/chunkedhtml-demo/8.22-markdown-variants.html
        # Joplin follows CommonMark: https://joplinapp.org/help/apps/markdown
        note_body = pypandoc.convert_file(file_, "commonmark_x")
    parent.child_notes.append(
        Note(
            {
                "title": file_.stem,
                "body": note_body,
                "user_created_time": file_.stat().st_ctime * 1000,
                "user_updated_time": file_.stat().st_mtime * 1000,
                "source_application": "joplin_custom_importer",
            }
        )
    )


def convert_all_inputs(inputs, app):
    # parent notebook
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    source_app = "Joplin Custom Importer" if app is None else app
    parent = Notebook({"title": f"{now} - Import from {source_app}"})
    for single_input in inputs:
        # Convert the input data to an intermediate representation
        # that can be used by the importer later.
        # Try to use an app specific converter. If there is none,
        # fall back to the default converter.
        try:
            module = importlib.import_module(f"apps.{app}")
            conversion_function = module.convert
        except ModuleNotFoundError:
            conversion_function = (
                convert_file if single_input.is_file() else convert_folder
            )
        # TODO: Children are added to the parent node / node tree implicitly.
        # This is an anti-pattern, but works for now.
        conversion_function(single_input, parent)
    return parent


def get_import_stats(parent, stats=None):
    if stats is None:
        stats = {"notebooks": 1, "notes": 0, "resources": 0, "tags": 0}

    # iterate through all notebooks
    for notebook in parent.child_notebooks:
        get_import_stats(notebook, stats)

    # assemble stats
    stats["notebooks"] += len(parent.child_notebooks)
    stats["notes"] += len(parent.child_notes)
    for note in parent.child_notes:
        stats["resources"] += len(note.resources)
        stats["tags"] += len(note.tags)

    return stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "input", type=Path, nargs="+", help="The input file(s) or folder(s)."
    )
    # specific apps that need a special handling
    parser.add_argument(
        "--app",
        choices=[module.name for module in pkgutil.iter_modules(apps.__path__)],
        help="The source application.",
    )
    parser.add_argument(
        "--clear-notes", action="store_true", help="Clear everything before importing."
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Don't connect to the Joplin API."
    )
    parser.add_argument(
        "--log-file",
        action="store_true",
        help="Create a log file next to the executable.",
    )
    args = parser.parse_args()

    setup_logging(args.log_file)

    if not args.dry_run:
        # create the connection to Joplin first to fail fast in case of a problem
        api = api_helper.get_api()

        if args.clear_notes:
            delete_everything = input(
                "[WARN ] Really clear everything and start from scratch? (yes/no): "
            )
            if delete_everything.lower() == "yes":
                LOGGER.info("Clear everything. Please wait.")
                api.delete_all_notebooks()
                api.delete_all_resources()
                api.delete_all_tags()
                LOGGER.info("Cleared everything successfully.")
            else:
                LOGGER.info("Clearing skipped. Importing anyway.")

    LOGGER.info(f"Importing notes from {' '.join(map(str, args.input))}")

    # Sanity check - do the input files / folders exist?
    for item in args.input:
        if not item.exists():
            LOGGER.error(f"{item.resolve()} doesn't exist.")
            return

    LOGGER.info("Start parsing")
    note_tree = convert_all_inputs(args.input, args.app)
    stats = get_import_stats(note_tree)
    if stats == {"notebooks": 1, "notes": 0, "resources": 0, "tags": 0}:
        LOGGER.info(f"Nothing to import.")
        return
    LOGGER.info(f"Finished parsing: {stats}")

    if not args.dry_run:
        LOGGER.info("Start import to Joplin")
        joplin_importer = importer.JoplinImporter(api)
        joplin_importer.import_notebook(note_tree)
        LOGGER.info(
            "Imported notes to Joplin successfully. "
            "Please verify that everything was imported."
        )


if __name__ == "__main__":
    main()
