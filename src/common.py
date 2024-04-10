"""Common functions."""

from datetime import datetime
import re


MARKDOWN_LINK_REGEX = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
WIKILINK_LINK_REGEX = re.compile(r"(!)?\[\[(.+?)(?:\|(.+?))?\]\]")


def get_markdown_links(text: str):
    return MARKDOWN_LINK_REGEX.findall(text)


def get_wikilink_links(text: str):
    return WIKILINK_LINK_REGEX.findall(text)


def current_unix_ms():
    return int(datetime.now().timestamp() * 1000)


def date_to_unix_ms(date_):
    # https://stackoverflow.com/a/61886944/7410886
    return int(
        datetime(year=date_.year, month=date_.month, day=date_.day).timestamp() * 1000
    )


def iso_to_unix_ms(iso_time):
    return int(datetime.fromisoformat(iso_time).timestamp() * 1000)
