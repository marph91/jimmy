"""Importer for many (note) formats to Joplin."""

import importlib
import logging
from pathlib import Path

from rich import print  # pylint: disable=redefined-builtin
from rich.logging import RichHandler
from rich.tree import Tree

import common
import converter
import importer
import intermediate_format as imf


LOGGER = logging.getLogger("jimmy")


def setup_logging(log_to_file: bool, stdout_log_level: str):
    LOGGER.handlers.clear()

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
    console_handler_formatter = logging.Formatter("%(message)s")
    console_handler = RichHandler(show_path=False)
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


def get_tree(root_notebooks: list[imf.Notebook], root_tree: Tree) -> Tree:
    for notebook in root_notebooks:
        new_root_notebook = root_tree.add("📘 " + notebook.data["title"])
        for note in notebook.child_notes:
            new_note = new_root_notebook.add("📖 " + note.data["title"])
            for resource in note.resources:
                new_note.add("🎴 " + (resource.title or resource.filename.name))
            for tag in note.tags:
                new_note.add("🔖 " + tag.data["title"])
            for note_link in note.note_links:
                new_note.add("🔗 " + note_link.title)
        get_tree(notebook.child_notebooks, new_root_notebook)
    return root_tree


def jimmy(api, config) -> common.Stats:
    if not config.dry_run and config.clear_notes:
        LOGGER.info("Clear everything. Please wait.")
        api.delete_all_notebooks()
        api.delete_all_resources()
        api.delete_all_tags()
        LOGGER.info("Cleared everything successfully.")

    inputs_str = " ".join(map(str, config.input))
    LOGGER.info(f'Importing notes from "{inputs_str}"')
    LOGGER.info("Start parsing")
    root_notebooks = convert_all_inputs(config.input, config.format)
    stats = common.get_import_stats(root_notebooks)
    LOGGER.info(f"Finished parsing: {stats}")
    if config.print_tree:
        print(get_tree(root_notebooks, Tree("Note Tree")))

    if not config.dry_run:
        LOGGER.info("Start import to Joplin")
        progress_bars = stats.create_progress_bars()
        for note_tree in root_notebooks:
            joplin_importer = importer.JoplinImporter(api, progress_bars)
            joplin_importer.import_notebook(note_tree)
            # We need another pass, since at the first pass
            # target note IDs are unknown.
            joplin_importer.link_notes(note_tree)
        LOGGER.info(
            "Imported notes to Joplin successfully. "
            "Please verify that everything was imported."
        )
    return stats
