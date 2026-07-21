"""Common functions for the conversion to Markdown."""

import re

# https://en.wikipedia.org/wiki/List_of_URI_schemes
web_schemes = [
    "file",
    "ftp",
    "http",
    "https",
    "imap",
    "irc",
    "udp",
    "tcp",
    "ntp",
    "app",
    "s3",
]


# Problem: "//" is part of many URI (between scheme and host).
# We need to exclude them to prevent unwanted conversions.
NEG_LOOKBEHINDS = "".join(f"(?<!{scheme}:)" for scheme in web_schemes)
double_slash_re = re.compile(rf"{NEG_LOOKBEHINDS}\/\/(.*?){NEG_LOOKBEHINDS}\/\/")
horizontal_line_re = re.compile(r"^-{3,}$", re.MULTILINE)
