"""Helper functions for text operations."""


def split_leading_trailing_whitespace(value: str) -> tuple[str, str, str]:
    r"""
    >>> split_leading_trailing_whitespace("")
    ('', '', '')
    >>> split_leading_trailing_whitespace("foo")
    ('', 'foo', '')
    >>> split_leading_trailing_whitespace("  foo")
    ('  ', 'foo', '')
    >>> split_leading_trailing_whitespace("foo ")
    ('', 'foo', ' ')
    >>> split_leading_trailing_whitespace(" foo bar ")
    (' ', 'foo bar', ' ')
    >>> split_leading_trailing_whitespace("\t foo bar\xa0 ")
    ('\t ', 'foo bar', '\xa0 ')
    """
    leading_whitespace_stop = len(value) - len(value.lstrip())
    trailing_whitespace_start = len(value.rstrip())
    return (
        value[:leading_whitespace_stop],
        value[leading_whitespace_stop:trailing_whitespace_start],
        value[trailing_whitespace_start:],
    )


def split_title_from_body(markdown_: str, h1: bool = True) -> tuple[str, str]:
    r"""
    >>> split_title_from_body("# heading\n\n b")
    ('heading', 'b')
    >>> split_title_from_body("heading\n\n b")
    ('', 'heading\n\n b')
    >>> split_title_from_body("heading\n\n b", h1=False)
    ('heading', 'b')
    >>> split_title_from_body("😄\n\n# heading")
    ('', '😄\n\n# heading')
    """
    if markdown_.startswith("# ") or not h1:
        try:
            title, body = markdown_.split("\n", maxsplit=1)
            title = title.lstrip("# ")
            body = body.lstrip()
        except ValueError:
            title = markdown_
            body = ""
    else:
        title = ""
        body = markdown_
    return title, body
