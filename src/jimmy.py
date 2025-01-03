"""Importer for many (note) formats to Markdown."""

import importlib
import logging

import pypandoc
from rich import print  # pylint: disable=redefined-builtin
from rich.logging import RichHandler
from rich.tree import Tree

import common
import converter
import filters
import importer
import intermediate_format as imf


LOGGER = logging.getLogger("jimmy")


def setup_logging(log_to_file: bool, stdout_log_level: str):
    LOGGER.handlers.clear()

    # setup the root logger, but don't propagate. We will log use our own
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
    console_handler = RichHandler(markup=True, show_path=False)
    console_handler.setFormatter(console_handler_formatter)
    console_handler.setLevel(stdout_log_level)
    LOGGER.addHandler(console_handler)

    # handle other loggers
    # https://stackoverflow.com/a/53250066/7410886
    other_loggers = [
        logging.getLogger(log)
        for log in ("anyblock_exporter", "pypandoc", "python-markdown")
    ]
    for log in other_loggers:
        log.propagate = False
        log.handlers.clear()
        log.setLevel(logging.WARNING)
        log.addHandler(console_handler)


def convert_all_inputs(config):
    """
    Convert the input data to an intermediate representation
    that can be used by the importer later.
    """
    # Try to use an app specific converter. If there is none,
    # fall back to the default converter.
    try:
        LOGGER.debug(f"Try converting with converter {config.format}")
        module = importlib.import_module(f"formats.{config.format}")
        converter_ = module.Converter(config)
    except ModuleNotFoundError as exc:
        LOGGER.debug(f"Fallback to default converter: {exc}")
        if str(exc) == f"No module named 'formats.{config.format}'":
            converter_ = converter.DefaultConverter(config)
        else:
            raise exc  # this is unexpected -> reraise
    # TODO: Children are added to the parent node / node tree implicitly.
    # This is an anti-pattern, but works for now.
    parent = converter_.convert_multiple(config.input)
    return parent


def get_tree(root_notebooks: imf.Notebooks, root_tree: Tree) -> Tree:
    for notebook in root_notebooks:
        new_root_notebook = root_tree.add("📘 " + notebook.title)
        for note in notebook.child_notes:
            new_note = new_root_notebook.add("📖 " + note.title)
            for resource in note.resources:
                new_note.add("🎴 " + (resource.title or resource.filename.name))
            for tag in note.tags:
                new_note.add("🔖 " + tag.title)
            for note_link in note.note_links:
                new_note.add("🔗 " + note_link.title)
        get_tree(notebook.child_notebooks, new_root_notebook)
    return root_tree


def get_jimmy_version():
    version_file = common.ROOT_PATH / ".version"
    return (
        version_file.read_text().lstrip("v").rstrip()
        if version_file.is_file()
        else "dev"
    )


def get_pandoc_version():
    try:
        return pypandoc.get_pandoc_version()
    except OSError:
        return "unknown"


def jimmy(config) -> common.Stats:
    LOGGER.info(f"Jimmy {get_jimmy_version()} (Pandoc {get_pandoc_version()})")
    inputs_str = " ".join(map(str, config.input))
    LOGGER.info(f'Importing notes from "{inputs_str}"')
    LOGGER.info("Start parsing")
    root_notebooks = convert_all_inputs(config)
    stats = common.get_import_stats(root_notebooks)
    LOGGER.info(f"Finished parsing: {stats}")
    if config.print_tree:
        print(get_tree(root_notebooks, Tree("Note Tree")))

    LOGGER.info("Start filtering")
    filters.apply_filters(root_notebooks, config)
    stats_filtered = common.get_import_stats(root_notebooks)
    LOGGER.info(f"Finished filtering: {stats}")
    if config.print_tree and stats != stats_filtered:
        print(get_tree(root_notebooks, Tree("Note Tree Filtered")))

    LOGGER.info("Start writing to file system")
    progress_bars = stats.create_progress_bars(config.no_progress_bars)
    for note_tree in root_notebooks:
        # first pass
        pd = importer.PathDeterminer(config)
        pd.determine_paths(note_tree)

        # second pass
        file_system_importer = importer.FilesystemImporter(
            progress_bars, config, stats, pd.note_id_map
        )
        file_system_importer.import_notebook(note_tree)

    LOGGER.info(
        "Converted notes successfully to Markdown: "
        f"[link={config.output_folder.resolve().as_uri()}]"
        f'"{config.output_folder.name}"[/link]. '
        "Please verify that everything was converted correctly."
    )
    LOGGER.info(
        "[bold]Feel free to open an issue on "
        "[link=https://github.com/marph91/jimmy/issues]Github[/link], "
        "write a message at the "
        "[link=https://discourse.joplinapp.org/t/jimmy-a-joplin-import-tool/38503]"
        "Joplin forum[/link], "
        "[link=https://forum.obsidian.md/t/jimmy-convert-your-notes-to-markdown/88685]"
        "Obsidian forum[/link] or an [link=mailto:martin.d@andix.de]email[/link]."
        "[/bold]"
    )

    return stats
