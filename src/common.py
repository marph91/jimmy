"""Common functions."""

import datetime as dt
import re


MARKDOWN_LINK_REGEX = re.compile(r"(!)?\[([^\]]+)\]\(([^)]+)\)")
WIKILINK_LINK_REGEX = re.compile(r"(!)?\[\[(.+?)(?:\|(.+?))?\]\]")


def get_markdown_links(text: str):
    return MARKDOWN_LINK_REGEX.findall(text)


def get_wikilink_links(text: str):
    return WIKILINK_LINK_REGEX.findall(text)


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
