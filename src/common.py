"""Common functions."""

from datetime import datetime


def iso_to_unix_ms(iso_time):
    return int(datetime.fromisoformat(iso_time).timestamp() * 1000)
