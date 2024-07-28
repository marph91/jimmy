"""CLI for jimmy."""

import argparse
import logging
from pathlib import Path

import api_helper
import common
import jimmy


LOGGER = logging.getLogger("jimmy")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "input", type=Path, nargs="+", help="The input file(s) or folder(s)."
    )
    # specific formats that need a special handling
    parser.add_argument(
        "--format",
        choices=common.get_available_formats(),
        help="The source format.",
    )
    parser.add_argument(
        "--clear-notes", action="store_true", help="Clear everything before importing."
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Don't connect to the Joplin API."
    )
    parser.add_argument(
        "--print-tree",
        action="store_true",
        help="Print the parsed note tree in intermediate format.",
    )
    parser.add_argument(
        "--log-file",
        action="store_true",
        help="Create a log file next to the executable.",
    )
    parser.add_argument(
        "--stdout-log-level",
        default="INFO",
        choices=logging._nameToLevel.keys(),  # pylint: disable=protected-access
        help="Create a log file next to the executable.",
    )

    filters = parser.add_mutually_exclusive_group(title="filters")
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

    jimmy.setup_logging(config.log_file, config.stdout_log_level)

    if config.clear_notes and not config.dry_run:
        delete_everything = input(
            "[WARN ] Really clear everything and start from scratch? (yes/no): "
        )
        if delete_everything.lower() not in ("y", "yes"):
            return

    if config.dry_run:
        api = None
    else:
        # create the connection to Joplin first to fail fast in case of a problem
        api = api_helper.get_api(LOGGER.info, LOGGER.error)
        if api is None:
            return

    jimmy.jimmy(api, config)


if __name__ == "__main__":
    main()
