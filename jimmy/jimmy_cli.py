"""CLI for jimmy."""

import argparse
import datetime
import logging
from pathlib import Path

import jimmy.common
import jimmy.main

LOGGER = logging.getLogger("jimmy")


def relative_path(path: str | Path | None) -> Path | None:
    """
    Checks if a path is relative.

    >>> str(relative_path("a"))
    'a'
    >>> relative_path("/a")
    Traceback (most recent call last):
    ...
    argparse.ArgumentTypeError: Please specify a relative path.
    >>> str(relative_path("~"))
    Traceback (most recent call last):
    ...
    argparse.ArgumentTypeError: Please specify a relative path.
    >>> relative_path("a/b")
    Traceback (most recent call last):
    ...
    argparse.ArgumentTypeError: Nested paths are not supported.
    >>> str(relative_path("a/"))
    'a'
    >>> str(relative_path("./a"))
    'a'
    """
    if path is None:
        return None
    # https://stackoverflow.com/a/37472037
    path_to_check = Path(path).expanduser()
    if path_to_check.is_absolute():
        raise argparse.ArgumentTypeError("Please specify a relative path.")
    if len(path_to_check.parts) > 1:
        raise argparse.ArgumentTypeError("Nested paths are not supported.")
    return path_to_check


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "input", type=Path, nargs="+", help="The input file(s) or folder(s)."
    )
    # specific formats that need a special handling
    parser.add_argument(
        "--format",
        choices=jimmy.common.get_available_formats(),
        help="The source format.",
    )
    parser.add_argument(
        "--password",
        default="",
        help="Password to decrypt the input.",
    )
    parser.add_argument(
        "--frontmatter",
        default=None,
        choices=(None, "joplin", "obsidian", "qownnotes"),
        help="Frontmatter type.",
    )
    # TODO: document
    parser.add_argument(
        "--template-file",
        type=Path,
        help="Path to a template file, applied to the note body.",
    )
    parser.add_argument(
        "--output-folder",
        type=Path,
        help="The output folder.",
    )
    parser.add_argument(
        "--global-resource-folder",
        type=relative_path,
        help="The resource folder for images, PDF and other data. "
        "Relative to the output folder.",
    )
    parser.add_argument(
        "--local-resource-folder",
        type=relative_path,
        help="The resource folder for images, PDF and other data. "
        "Relative to the location of the corresponding note.",
        default=Path("."),  # next to the note
    )
    parser.add_argument(
        "--local-image-folder",
        type=relative_path,
        help="The folder for images. Works only together with "
        "--local-resource-folder. "
        "Relative to the location of the corresponding note.",
    )
    parser.add_argument(
        "--print-tree",
        action="store_true",
        help="Print the parsed note tree in intermediate format.",
    )
    parser.add_argument("--log-file", type=Path, help="Path for the log file.")
    parser.add_argument(
        "--no-stdout-log", action="store_true", help="Don't log to stdout."
    )
    parser.add_argument(
        "--stdout-log-level",
        default="INFO",
        choices=logging._nameToLevel.keys(),  # pylint: disable=protected-access
        help="Create a log file next to the executable.",
    )

    filters = parser.add_mutually_exclusive_group()
    filters.add_argument("--exclude-notes", nargs="+", help="Exclude notes by title.")
    filters.add_argument("--include-notes", nargs="+", help="Include notes by title.")
    filters.add_argument(
        "--exclude-notes-with-tags", nargs="+", help="Exclude notes with tag."
    )
    filters.add_argument(
        "--include-notes-with-tags", nargs="+", help="Include notes with tag."
    )
    filters.add_argument("--exclude-tags", nargs="+", help="Exclude tags.")
    filters.add_argument("--include-tags", nargs="+", help="Include tags.")

    config = parser.parse_args()

    if config.output_folder is None:
        # If there is no output folder specified, just put
        # the output next to the first input.
        now = datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%SZ")
        format_ = "filesystem" if config.format is None else config.format
        config.output_folder = (
            config.input[0].parent / f"{now} - Jimmy Import from {format_}"
        )

    jimmy.main.setup_logging(
        no_stdout_log=config.no_stdout_log,
        stdout_log_level=config.stdout_log_level,
        log_file=config.log_file,
    )

    jimmy.main.run_conversion(config)


if __name__ == "__main__":
    main()
