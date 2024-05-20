"""Importer for many (note) formats to Joplin."""

from dataclasses import dataclass
import importlib
import logging
from pathlib import Path

import converter
import importer
import intermediate_format as imf


LOGGER = logging.getLogger("jimmy")


def setup_logging(log_to_file: bool, stdout_log_level: str):
    if LOGGER.handlers:
        # Don't setup handlers again. This results in duplicated logging.
        # TODO: This is a problem if the arguments change.
        return

    # mute other loggers
    # https://stackoverflow.com/a/53250066/7410886
    logging.getLogger("pypandoc").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("joppy").setLevel(logging.WARNING)
    logging.getLogger("python-markdown").setLevel(logging.WARNING)

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
    console_handler.setLevel(stdout_log_level)
    LOGGER.addHandler(console_handler)


def convert_all_inputs(inputs: list[Path], format_: str):
    """
    Convert the input data to an intermediate representation
    that can be used by the importer later.
    """
    # Try to use an app specific converter. If there is none,
    # fall back to the default converter.
    try:
        LOGGER.debug(f"Try converting with converter {format_}")
        module = importlib.import_module(f"formats.{format_}")
        converter_ = module.Converter(format_)
    except ModuleNotFoundError as exc:
        LOGGER.debug(f"Fallback to default converter: {exc}")
        if str(exc) == f"No module named 'formats.{format_}'":
            converter_ = converter.DefaultConverter(format_)
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

    def __str__(self):
        if self == Stats():
            return "nothing"
        stats = []
        if self.notebooks > 0:
            stats.append(f"{self.notebooks} notebooks")
        if self.notes > 0:
            stats.append(f"{self.notes} notes")
        if self.resources > 0:
            stats.append(f"{self.resources} resources")
        if self.tags > 0:
            stats.append(f"{self.tags} tags")
        if self.note_links > 0:
            stats.append(f"{self.note_links} note links")
        return ", ".join(stats)


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


def jimmy(api, config):
    setup_logging(config.log_file, config.stdout_log_level)

    if not config.dry_run:
        if config.clear_notes:
            LOGGER.info("Clear everything. Please wait.")
            api.delete_all_notebooks()
            api.delete_all_resources()
            api.delete_all_tags()
            LOGGER.info("Cleared everything successfully.")

    LOGGER.info(f"Importing notes from {' '.join(map(str, config.input))}")
    LOGGER.info("Start parsing")
    root_notebooks = convert_all_inputs(config.input, config.format)
    stats = get_import_stats(root_notebooks)
    LOGGER.info(f"Finished parsing: {stats}")

    if not config.dry_run:
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
    return stats
