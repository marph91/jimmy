"""Common functions."""

import datetime as dt
import logging
from pathlib import Path
import re
import tempfile
import time

import pypandoc


LOGGER = logging.getLogger("joplin_custom_importer")


###########################################################
# operations on note body
###########################################################


def try_transfer_dicts(source: dict, target: dict, keys: list[str | tuple[str, str]]):
    """Try to transfer values from one to another dict if they exist."""
    for key in keys:
        if isinstance(key, tuple):
            source_key, target_key = key
        else:
            source_key = target_key = key
        if (value := source.get(source_key)) is not None:
            target[target_key] = value


###########################################################
# operations on note body
###########################################################

MARKDOWN_LINK_REGEX = re.compile(r"(!)?\[([^\]]*)\]\(([^)]+)\)")
WIKILINK_LINK_REGEX = re.compile(r"(!)?\[\[(.+?)(?:\|(.+?))?\]\]")


def get_markdown_links(text: str) -> list:
    return MARKDOWN_LINK_REGEX.findall(text)


def get_wikilink_links(text: str) -> list:
    return WIKILINK_LINK_REGEX.findall(text)


def get_inline_tags(text: str, start_characters: list[str]) -> list[str]:
    """
    >>> get_inline_tags("# header", ["#"])
    []
    >>> get_inline_tags("#tag", ["#"])
    ['tag']
    >>> get_inline_tags("#tag abc", ["#"])
    ['tag']
    >>> sorted(get_inline_tags("#tag @abc", ["#", "@"]))
    ['abc', 'tag']
    """
    # TODO: can possibly be combined with todoist.split_labels()
    tags = set()
    for word in text.split():
        if any(word.startswith(char) for char in start_characters) and len(word) > 1:
            tags.add(word[1:])
    return list(tags)


def html_text_to_markdown(html_text: str) -> str:
    # Don't use "commonmark_x". There would be too many noise.
    return pypandoc.convert_text(
        html_text, "markdown_strict+pipe_tables-raw_html", format="html"
    )


###########################################################
# folder operations
###########################################################


def get_temp_folder() -> Path:
    return Path(tempfile.gettempdir()) / f"joplin_export_{int(time.time())}"


def find_file_recursively(root_folder: Path, url: str) -> Path | None:
    potential_matches = list(root_folder.glob(f"**/{url}"))
    if not potential_matches:
        LOGGER.debug(f"Couldn't find match for resource {url}")
        return None
    if len(potential_matches) > 1:
        LOGGER.debug(f"Found too many matches for resource {url}")
    return potential_matches[0]


###########################################################
# datetime helpers
###########################################################


def get_ctime_mtime_ms(item: Path) -> dict:
    data = {}
    if (ctime_ms := int(item.stat().st_ctime * 1000)) > 0:
        data["user_created_time"] = ctime_ms
    if (mtime_ms := int(item.stat().st_mtime * 1000)) > 0:
        data["user_updated_time"] = mtime_ms
    return data


def datetime_to_ms(datetime_: dt.datetime) -> int:
    return int(datetime_.timestamp() * 1000)


def current_unix_ms() -> int:
    return datetime_to_ms(dt.datetime.now())


def date_to_unix_ms(date_: dt.date) -> int:
    # https://stackoverflow.com/a/61886944/7410886
    return datetime_to_ms(
        dt.datetime(year=date_.year, month=date_.month, day=date_.day)
    )


def iso_to_unix_ms(iso_time: str) -> int:
    return datetime_to_ms(dt.datetime.fromisoformat(iso_time))
