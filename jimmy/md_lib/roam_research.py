"""Convert Roam Research to Markdown."""

import re

import pyparsing as pp


any_link_re = re.compile(r"{{\[\[\S+\]\]: (\S+)}}")


def tag():
    def to_md(_, t):  # noqa
        return "#" + t[0].replace(" ", "-")  # TODO: How to handle whitespaces in tags?

    return pp.QuotedString("#[[", end_quote_char="]]").set_parse_action(to_md)


def highlight():
    def to_md(_, t):  # noqa
        return "==" + t[0] + "=="

    return pp.QuotedString("^^").set_parse_action(to_md)


def italic():
    def to_md(_, t):  # noqa
        return "*" + t[0] + "*"

    return pp.QuotedString("__").set_parse_action(to_md)


def any_link():
    def to_md(_, t):  # noqa
        if t[0][0].startswith("http"):
            return f"<{t[0][0]}>"
        return t[0][0]

    return pp.Regex(any_link_re, as_group_list=True).set_parse_action(to_md)


def roam_internal_function():
    def to_md(_, t):  # noqa
        return "{{[[" + t[0] + "]]}}"  # return the original string, but don't process further

    return pp.QuotedString("{{[[", end_quote_char="]]}}").set_parse_action(to_md)


def is_block_id(value: str) -> bool:
    return len(value) == 9 and value.isalnum()


def block_link():
    def to_md(_, t):  # noqa
        title = t[0]
        if is_block_id(title):
            return f"[{title}](roam-block://{title})"
        return "((" + title + "))"

    return pp.QuotedString("((", end_quote_char="))").set_parse_action(to_md)


def block_link_in_md_link():
    def to_md(_, t):  # noqa
        title = t[0]
        if is_block_id(title):
            return f"](roam-block://{title})"
        return "](((" + title + ")))"

    return pp.QuotedString("](((", end_quote_char=")))").set_parse_action(to_md)


def embedded_block():
    def to_md(_, t):  # noqa
        title = t[0]
        return f"[{title}](roam-block://{title})"

    return pp.QuotedString("{{[[embed]]: ((", end_quote_char="))}}").set_parse_action(to_md)


def page_link():
    def to_md(_, t):  # noqa
        title = t[0]
        return f"[{title}](roam-page://{title})"

    return pp.QuotedString("[[", end_quote_char="]]").set_parse_action(to_md)


def page_link_in_md_link():
    def to_md(_, t):  # noqa
        title = t[0]
        return f"](roam-page://{title})"

    return pp.QuotedString("]([[", end_quote_char="]])").set_parse_action(to_md)


def embedded_mentioned_page():
    def to_md(_, t):  # noqa
        title = t[0]
        return f"[{title}](roam-page://{title})"

    return (
        pp.QuotedString("{{[[embed]]: [[", end_quote_char="]]}}")
        | pp.QuotedString("{{[[mentions]]: [[", end_quote_char="]]}}")
    ).set_parse_action(to_md)


def roam_to_md(roam_text: str) -> str:
    r"""
    Main Roam Research to Markdown conversion function.

    >>> roam_to_md("^^highlighted^^")
    '==highlighted=='
    >>> roam_to_md("#tag #[[another tag]]")
    '#tag #another-tag'
    >>> roam_to_md("- {{[[TODO]]}} check\n- {{[[DONE]]}} list")
    '- [ ] check\n- [x] list'
    >>> roam_to_md("> citation 1\n[[>]] citation 2")
    '> citation 1\n> citation 2'
    >>> roam_to_md("[link to page]([[Theme Tester]])")
    '[link to page](roam-page://Theme Tester)'
    >>> roam_to_md("[link to block](((JF3iFJPKu)))")
    '[link to block](roam-block://JF3iFJPKu)'
    >>> roam_to_md("[[link to page]]")
    '[link to page](roam-page://link to page)'
    >>> roam_to_md("[[August 5th, 2023]]")
    '[August 5th, 2023](roam-page://August 5th, 2023)'
    >>> roam_to_md("embedded block: {{[[embed]]: ((sHQRa0Wan))}}")
    'embedded block: [sHQRa0Wan](roam-block://sHQRa0Wan)'
    >>> roam_to_md("embedded page: {{[[embed]]: [[testing]]}}")
    'embedded page: [testing](roam-page://testing)'
    >>> roam_to_md("mentioned page: {{[[mentions]]: [[White Paper]]}}")
    'mentioned page: [White Paper](roam-page://White Paper)'
    >>> roam_to_md("{{[[slider]]}}")
    '{{[[slider]]}}'
    >>> roam_to_md("{{[[table]]}}")
    '{{[[table]]}}'
    >>> roam_to_md("((aaa))")
    '((aaa))'
    >>> roam_to_md("{{[[pdf]]: https://some.url/abc.pdf}}")
    '<https://some.url/abc.pdf>'
    """

    roam_markup = (
        tag()
        | highlight()
        | italic()
        | embedded_block()
        | block_link_in_md_link()
        | block_link()
        | embedded_mentioned_page()
        | page_link_in_md_link()
        | any_link()
        | roam_internal_function()
        | page_link()
    )

    roam_text = roam_text.replace("{{[[TODO]]}}", "[ ]")
    roam_text = roam_text.replace("{{[[DONE]]}}", "[x]")
    roam_text = roam_text.replace("[[>]]", ">")
    return roam_markup.transform_string(roam_text)
