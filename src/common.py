"""Common functions."""

from datetime import datetime


def current_unix_ms():
    return int(datetime.now().timestamp() * 1000)


def date_to_unix_ms(date_):
    # https://stackoverflow.com/a/61886944/7410886
    return int(
        datetime(year=date_.year, month=date_.month, day=date_.day).timestamp() * 1000
    )


def iso_to_unix_ms(iso_time):
    return int(datetime.fromisoformat(iso_time).timestamp() * 1000)
