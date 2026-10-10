"""Converter for many (note) formats to Markdown."""

import logging
import os
from pathlib import Path
import shutil

import pypandoc
from rich import print  # pylint: disable=redefined-builtin
from rich.tree import Tree

from jimmy import (
    common,
    converter,
    filters,
    intermediate_format as imf,
    variables,
    writer,
)
lazy import jimmy.formats.affine
lazy import jimmy.formats.anki
lazy import jimmy.formats.anytype
lazy import jimmy.formats.bear
lazy import jimmy.formats.cacher
lazy import jimmy.formats.cherrytree
lazy import jimmy.formats.clipto
lazy import jimmy.formats.colornote
lazy import jimmy.formats.day_one
lazy import jimmy.formats.diaro
lazy import jimmy.formats.drafts
lazy import jimmy.formats.dynalist
lazy import jimmy.formats.evernote
lazy import jimmy.formats.facebook
lazy import jimmy.formats.google_docs
lazy import jimmy.formats.google_keep
lazy import jimmy.formats.joplin
lazy import jimmy.formats.jrnl
lazy import jimmy.formats.nimbus_note
lazy import jimmy.formats.notion
lazy import jimmy.formats.obsidian
lazy import jimmy.formats.qownnotes
lazy import jimmy.formats.rednotebook
lazy import jimmy.formats.reflect
lazy import jimmy.formats.roam_research
lazy import jimmy.formats.signal
lazy import jimmy.formats.simplenote
lazy import jimmy.formats.standard_notes
lazy import jimmy.formats.synology_note_station
lazy import jimmy.formats.telegram
lazy import jimmy.formats.textbundle
lazy import jimmy.formats.tiddlywiki
lazy import jimmy.formats.tomboy_ng
lazy import jimmy.formats.turtl
lazy import jimmy.formats.upnote
lazy import jimmy.formats.wordpress
lazy import jimmy.formats.zettelkasten
lazy import jimmy.formats.zim
lazy import jimmy.formats.zoho_notebook

LOGGER = logging.getLogger("jimmy")


def add_binaries_to_path():
    # Extend the path here, since it's needed for CLI and TUI.
    # Search for the local/pyinstaller binaries first.
    # https://pyinstaller.org/en/stable/runtime-information.html#using-file
    binaries_folder = str(Path(__file__).parent.parent.parent / "bin")
    if binaries_folder not in os.environ["PATH"]:
        os.environ["PATH"] = binaries_folder + os.pathsep + os.environ["PATH"]


def setup_logging(custom_handlers: list | None = None):
    LOGGER.handlers.clear()

    # setup the root logger, but don't propagate. We will log use our own
    # log handler. See: https://stackoverflow.com/a/71365918/7410886
    logging.basicConfig(level=logging.DEBUG)
    LOGGER.propagate = False

    if custom_handlers is None:
        custom_handlers = []
    for custom_handler in custom_handlers:
        LOGGER.addHandler(custom_handler)

    # handle other loggers
    # https://stackoverflow.com/a/53250066/7410886
    other_loggers = [
        logging.getLogger(log)
        for log in (
            "anyblock_exporter",
            "asyncio",
            # "markdown_it",
            "pdf_oxide",
            "pypandoc",
            "python-markdown",
            "watchdog",
        )
    ]
    for log in other_loggers:
        log.propagate = False
        log.handlers.clear()
        log.setLevel(logging.ERROR)


def convert_all_inputs(config) -> tuple[imf.Notebooks, int]:
    """
    Convert the input data to an intermediate representation
    that can be used by the writer later.
    """
    if config.format is None:
        LOGGER.debug("Converting with default converter.")
        converter_ = converter.DefaultConverter(config)
    elif config.format not in variables.FORMAT_REGISTRY:
        raise NotImplementedError(f"There is no converter for {config.format}!")
    else:
        match config.format:  # TODO: merge with variables.FORMAT_REGISTRY?
            case "affine":
                converter_module = jimmy.formats.affine
            case "anki":
                converter_module = jimmy.formats.anki
            case "anytype":
                converter_module = jimmy.formats.anytype
            case "bear":
                converter_module = jimmy.formats.bear
            case "cacher":
                converter_module = jimmy.formats.cacher
            case "cherrytree":
                converter_module = jimmy.formats.cherrytree
            case "clipto":
                converter_module = jimmy.formats.clipto
            case "colornote":
                converter_module = jimmy.formats.colornote
            case "day_one":
                converter_module = jimmy.formats.day_one
            case "diaro":
                converter_module = jimmy.formats.diaro
            case "drafts":
                converter_module = jimmy.formats.drafts
            case "dynalist":
                converter_module = jimmy.formats.dynalist
            case "evernote":
                converter_module = jimmy.formats.evernote
            case "facebook":
                converter_module = jimmy.formats.facebook
            case "google_docs":
                converter_module = jimmy.formats.google_docs
            case "google_keep":
                converter_module = jimmy.formats.google_keep
            case "joplin":
                converter_module = jimmy.formats.joplin
            case "jrnl":
                converter_module = jimmy.formats.jrnl
            case "nimbus_note":
                converter_module = jimmy.formats.nimbus_note
            case "notion":
                converter_module = jimmy.formats.notion
            case "obsidian":
                converter_module = jimmy.formats.obsidian
            case "qownnotes":
                converter_module = jimmy.formats.qownnotes
            case "rednotebook":
                converter_module = jimmy.formats.rednotebook
            case "reflect":
                converter_module = jimmy.formats.reflect
            case "roam_research":
                converter_module = jimmy.formats.roam_research
            case "signal":
                converter_module = jimmy.formats.signal
            case "simplenote":
                converter_module = jimmy.formats.simplenote
            case "standard_notes":
                converter_module = jimmy.formats.standard_notes
            case "synology_note_station":
                converter_module = jimmy.formats.synology_note_station
            case "telegram":
                converter_module = jimmy.formats.telegram
            case "textbundle":
                converter_module = jimmy.formats.textbundle
            case "tiddlywiki":
                converter_module = jimmy.formats.tiddlywiki
            case "tomboy_ng":
                converter_module = jimmy.formats.tomboy_ng
            case "turtl":
                converter_module = jimmy.formats.turtl
            case "upnote":
                converter_module = jimmy.formats.upnote
            case "wordpress":
                converter_module = jimmy.formats.wordpress
            case "zettelkasten":
                converter_module = jimmy.formats.zettelkasten
            case "zim":
                converter_module = jimmy.formats.zim
            case "zoho_notebook":
                converter_module = jimmy.formats.zoho_notebook
            case _:
                raise NotImplementedError(f"There is no converter for {config.format}!")
        converter_ = converter_module.Converter(config)
        LOGGER.debug(f'Converting with converter "{config.format}"')

    # Children are added to the parent node / node tree implicitly.
    # This is an anti-pattern, but works for now.
    parent, errors = converter_.convert_multiple(config.input)
    return parent, errors


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


def get_pandoc_version() -> str:
    try:
        return pypandoc.get_pandoc_version()
    except OSError:
        return "unknown"


def run_conversion(config) -> tuple[common.Stats, int]:
    LOGGER.info(f"Jimmy {variables.VERSION} (Pandoc {get_pandoc_version()})")
    LOGGER.debug(f"Using pandoc from: {shutil.which('pandoc')}")
    LOGGER.debug(f"{config=}")
    inputs_str = " ".join(map(str, config.input))
    LOGGER.info(f'Converting notes from "{inputs_str}"')
    LOGGER.info(
        "Start parsing. This may take some time. "
        'The extended log can be enabled by "--stdout-log-level DEBUG".'
    )
    root_notebooks, errors = convert_all_inputs(config)
    stats = common.get_import_stats(root_notebooks)

    # return early, if each input errored or there were no notes converted
    if errors >= len(config.input) or stats.notes == 0:
        return stats, errors

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

    return stats, errors
