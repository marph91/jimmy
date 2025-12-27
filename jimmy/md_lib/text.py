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


def to_markdown_header_id(text: str) -> str:
    """
    Convert any (header) text to a Markdown header ID.
    See: https://pandoc.org/MANUAL.html#extension-auto_identifiers
    Slightly adapted to work in Firefox and VSCode.

    >>> to_markdown_header_id("Heading identifiers in HTML")
    'heading-identifiers-in-html'
    >>> to_markdown_header_id("Maître d'hôtel")
    'maître-dhôtel'
    >>> to_markdown_header_id("*Dogs*?--in *my* house?")
    'dogs--in-my-house'
    >>> to_markdown_header_id("[HTML], [S5], or [RTF]?")
    'html-s5-or-rtf'
    >>> to_markdown_header_id("3. Applications")
    '3-applications'
    >>> to_markdown_header_id("4-х актная  структура выступления (монолога)")
    '4-х-актная-структура-выступления-монолога'
    >>> to_markdown_header_id("")
    ''
    >>> to_markdown_header_id(" ")
    'section'
    """
    if not text:
        return text
    # Reduce consecutive whitespaces.
    text = " ".join(text.split())
    # Remove all non-alphanumeric characters, except underscores, hyphens, and periods.
    text = "".join(
        [character for character in text if (character.isalnum() or character in (" ", "_", "-"))]
    )
    # Replace all spaces and newlines with hyphens.
    text = text.replace(" ", "-").replace("\n", "-")
    # Convert all alphabetic characters to lowercase.
    text = text.lower()
    # Remove everything up to the first letter (identifiers may not begin with a number
    # or punctuation mark).
    new_text = []
    found_first_letter = False
    for character in text:
        if character.isalnum() or found_first_letter:
            new_text.append(character)
            found_first_letter = True
    text = "".join(new_text)
    # If nothing is left after this, use the identifier section.
    if not text:
        text = "section"
    return text
