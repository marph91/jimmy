"""Convert ColorNote markup to Markdown."""

import re

import pyparsing as pp


list_re = re.compile(r"^(\[[ V]\] )", re.MULTILINE)


def list_():
    def to_md(_, t):  # noqa
        match = t[0][0]
        list_character = {"[ ] ": "- [ ] ", "[V] ": "- [x] "}[match]
        return list_character

    return pp.Regex(list_re, as_group_list=True).set_parse_action(to_md)


def colornote_to_md(body: str) -> str:
    r"""
    Main ColorNote markup to Markdown conversion function.

    >>> colornote_to_md("[V] A\n[V] B")
    '- [x] A\n- [x] B'
    >>> colornote_to_md("[ ] Item 1\n[ ] Item 2\n[ ] Item 3")
    '- [ ] Item 1\n- [ ] Item 2\n- [ ] Item 3'
    """
    markup = list_()
    return markup.transform_string(body)
