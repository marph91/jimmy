"""Converter for many (note) formats to Markdown."""

import importlib
import logging
from pathlib import Path

import pypandoc
from rich import print  # pylint: disable=redefined-builtin
from rich.logging import RichHandler
from rich.tree import Tree

from jimmy import (
    common,
    converter,
    filters,
    writer,
    intermediate_format as imf,
    version,
)


LOGGER = logging.getLogger("jimmy")


def setup_logging(
    no_stdout_log: bool = True,
    stdout_log_level: str = "DEBUG",
    log_file: str | Path | None = None,
):
    LOGGER.handlers.clear()

    # setup the root logger, but don't propagate. We will log use our own
    # log handler. See: https://stackoverflow.com/a/71365918/7410886
    logging.basicConfig(level=logging.DEBUG)
    LOGGER.propagate = False

    if log_file is not None:
        # log to file
        file_handler_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)-5.5s]  %(message)s"
        )
        file_handler = logging.FileHandler(log_file, mode="w")
        file_handler.setFormatter(file_handler_formatter)
        file_handler.setLevel(logging.DEBUG)
        LOGGER.addHandler(file_handler)

    if not no_stdout_log:
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
        for log in ("anyblock_exporter", "pypandoc", "python-markdown", "watchdog")
    ]
    for log in other_loggers:
        log.propagate = False
        log.handlers.clear()
        log.setLevel(logging.WARNING)
        if not no_stdout_log:
            log.addHandler(console_handler)


def convert_all_inputs(config):
    """
    Convert the input data to an intermediate representation
    that can be used by the writer later.
    """
    # Try to use an app specific converter. If there is none,
    # fall back to the default converter.
    try:
        LOGGER.debug(f'Try converting with converter "{config.format}"')
        module = importlib.import_module(f"jimmy.formats.{config.format}")
        converter_ = module.Converter(config)
    except ModuleNotFoundError as exc:
        LOGGER.debug(f"Fallback to default converter: {exc}")
        if str(exc) == f"No module named 'jimmy.formats.{config.format}'":
            converter_ = converter.DefaultConverter(config)
        else:
            raise exc  # this is unexpected -> reraise
    # Children are added to the parent node / node tree implicitly.
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


def get_pandoc_version():
    try:
        return pypandoc.get_pandoc_version()
    except OSError:
        return "unknown"


def run_conversion(config) -> common.Stats:
    LOGGER.info(f"Jimmy {version.VERSION} (Pandoc {get_pandoc_version()})")
    inputs_str = " ".join(map(str, config.input))
    LOGGER.info(f'Converting notes from "{inputs_str}"')
    LOGGER.info(
        "Start parsing. This may take some time. "
        'The extended log can be enabled by "--stdout-log-level DEBUG".'
    )
    root_notebooks = convert_all_inputs(config)
    stats = common.get_import_stats(root_notebooks)
    LOGGER.info(f"Finished parsing: {stats}")
    if config.print_tree:
        print(get_tree(root_notebooks, Tree("Note Tree")))

    LOGGER.info("Start filtering")
    filters.apply_filters(root_notebooks, config)
    stats_filtered = common.get_import_stats(root_notebooks)
    LOGGER.info(f"Finished filtering: {stats_filtered}")
    if config.print_tree and stats != stats_filtered:
        print(get_tree(root_notebooks, Tree("Note Tree Filtered")))

    LOGGER.info("Start writing to file system")
    if stats.tags > 0 and not (config.frontmatter or config.template_file):
        LOGGER.warning(
            "Parsed tags will be lost without frontmatter. "
            'Frontmatter can be added by "--frontmatter joplin".'
        )
    stats_written = common.Stats()
    for note_tree in root_notebooks:
        # first pass
        pd = writer.PathDeterminer(config)
        pd.determine_paths(note_tree)

        # second pass
        file_system_writer = writer.FilesystemWriter(pd.note_id_map, stats_written)
        file_system_writer.write_notebook(note_tree)
    LOGGER.info(f"Finished writing to file system: {stats_written}")
    LOGGER.info(
        "Converted files were written to: "
        f"[link={config.output_folder.resolve().as_uri()}]"
        f'"{config.output_folder.name}"[/link]. '
    )

    # Resources might be skipped if duplicated.
    if (
        stats_filtered.notebooks == stats_written.notebooks
        and stats_filtered.notes == stats_written.notes
    ):
        LOGGER.info(
            "Converted notes successfully to Markdown. "
            "Please verify that everything was converted correctly."
        )
    else:
        LOGGER.warning(
            "Not all notes could be imported. "
            'Enable the extended log by "--stdout-log-level DEBUG".'
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
