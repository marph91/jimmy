"""Convert Zim Wiki to Markdown."""

import re

import pyparsing as pp

import markdown_lib.common


# Prevent spaces, tabs and newlines from being stripped.
pp.ParserElement.set_default_whitespace_chars("")


heading_re = re.compile(r"(={1,6}) (.*?) ={1,6}")
checklist_re = re.compile(r"^( *)\[([ <>*x])\] ", re.MULTILINE)


def quote(source_tag, target_tag):
    """Conversion of a quoted string. I. e. with the same start and end tags."""

    def to_md(_, t):  # noqa
        return target_tag + t[0] + target_tag

    return pp.QuotedString(source_tag).set_parse_action(to_md)


def subscript():
    def to_md(_, t):  # noqa
        return "~" + t[0] + "~"

    return pp.QuotedString("_{", endQuoteChar="}").set_parse_action(to_md)


def superscript():
    def to_md(_, t):  # noqa
        return "^" + t[0] + "^"

    return pp.QuotedString("^{", endQuoteChar="}").set_parse_action(to_md)


def italic():
    def to_md(_, t):  # noqa
        return "*" + t[0][0] + "*"

    return pp.Regex(
        markdown_lib.common.double_slash_re, as_group_list=True
    ).set_parse_action(to_md)


def horizontal_line():
    return pp.Regex(markdown_lib.common.horizontal_line_re).set_parse_action(
        lambda: "\n---\n"
    )


def heading():
    def to_md(_, t):  # noqa
        return "#" * (7 - len(t[0][0])) + " " + t[0][1]

    return pp.Regex(heading_re, as_group_list=True).set_parse_action(to_md)


def checklist():
    def to_md(_, t):  # noqa
        list_char = "x" if t[0][1] in ("*", "x") else " "
        return f"{t[0][0]}- [{list_char}] "

    return pp.Regex(checklist_re, as_group_list=True).set_parse_action(to_md)


def zim_to_md(zim_text: str) -> str:
    r"""
    Main Zim Wiki to Markdown conversion function.

    >>> zim_to_md("''monospace'' **bold**")
    '`monospace` **bold**'
    >>> zim_to_md("super^{script}, sub_{script}")
    'super^script^, sub~script~'
    >>> zim_to_md("====== heading 1 ======")
    '# heading 1'
    >>> zim_to_md("== heading5 ==")
    '##### heading5'
    >>> zim_to_md("'''\nsome code\nblock\n'''")
    '```\nsome code\nblock\n```'
    >>> zim_to_md("[ ] unchecked\n[x] not done")
    '- [ ] unchecked\n- [x] not done'
    >>> zim_to_md("[ ] u\n    [>] np\n    [*] nd\n[x] nd")
    '- [ ] u\n    - [ ] np\n    - [x] nd\n- [x] nd'
    >>> zim_to_md("* lvl1\n\t* lvl2\n\t* lvl2\n* lvl1")
    '* lvl1\n    * lvl2\n    * lvl2\n* lvl1'
    """
    zim_markup = (
        pp.Literal("'''").set_parse_action(lambda: "```")
        # text formatting
        | quote("''", "`")
        | italic()
        | subscript()
        | superscript()
        #
        | horizontal_line()
        | heading()
        | checklist()
    )

    # TODO: str.translate() seems to be fastest
    # https://stackoverflow.com/a/8958372
    zim_text = zim_text.replace("\t", " " * 4)
    return zim_markup.transform_string(zim_text)
