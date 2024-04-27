"""Importer for many (note) formats to Joplin."""

import argparse
from dataclasses import dataclass
import importlib
import logging
from pathlib import Path
import pkgutil

import api_helper
import apps
import converter
import importer
import intermediate_format as imf


LOGGER = logging.getLogger("jimmy")


def setup_logging(log_to_file: bool):
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
        file_handler = logging.FileHandler("jimmy.log", mode="w")
        file_handler.setFormatter(file_handler_formatter)
        file_handler.setLevel(logging.DEBUG)
        LOGGER.addHandler(file_handler)

    # log to stdout
    console_handler_formatter = logging.Formatter("[%(levelname)-5.5s] %(message)s")
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_handler_formatter)
    console_handler.setLevel(logging.INFO)
    LOGGER.addHandler(console_handler)


def convert_all_inputs(inputs: list[Path], app: str):
    # Convert the input data to an intermediate representation
    # that can be used by the importer later.
    # Try to use an app specific converter. If there is none,
    # fall back to the default converter.
    try:
        LOGGER.debug(f"Try converting with converter {app}")
        module = importlib.import_module(f"apps.{app}")
        converter_ = module.Converter(app)
    except ModuleNotFoundError as exc:
        LOGGER.debug(f"Fallback to default converter: {exc}")
        if str(exc) == f"No module named 'apps.{app}'":
            converter_ = converter.DefaultConverter(app)
        else:
            raise exc  # this is unexpected -> reraise
    # TODO: Children are added to the parent node / node tree implicitly.
    # This is an anti-pattern, but works for now.
    parent = converter_.convert_multiple(inputs)
    return parent


@dataclass
class Stats:
    notebooks: int = 0
    notes: int = 0
    resources: int = 0
    tags: int = 0
    note_links: int = 0


def get_import_stats(parents: list[imf.Notebook], stats: Stats | None = None) -> Stats:
    if stats is None:
        stats = Stats(len(parents))

    # iterate through all separate inputs
    for parent in parents:
        # iterate through all notebooks
        for notebook in parent.child_notebooks:
            get_import_stats([notebook], stats)

        # assemble stats
        stats.notebooks += len(parent.child_notebooks)
        stats.notes += len(parent.child_notes)
        for note in parent.child_notes:
            stats.resources += len(note.resources)
            stats.tags += len(note.tags)
            stats.note_links += len(note.note_links)

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
    root_notebooks = convert_all_inputs(args.input, args.app)
    stats = get_import_stats(root_notebooks)
    if stats == Stats(notebooks=1):
        LOGGER.info("Nothing to import.")
        return
    LOGGER.info(f"Finished parsing: {stats}")

    if not args.dry_run:
        LOGGER.info("Start import to Joplin")
        for note_tree in root_notebooks:
            joplin_importer = importer.JoplinImporter(api)
            joplin_importer.import_notebook(note_tree)
            # We need another pass, since at the first pass
            # target note IDs are unknown.
            joplin_importer.link_notes(note_tree)
        LOGGER.info(
            "Imported notes to Joplin successfully. "
            "Please verify that everything was imported."
        )


if __name__ == "__main__":
    main()
