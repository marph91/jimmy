"""Convert TiddlyWiki wikitext to Markdown."""

import logging
import re
import urllib.parse

import pyparsing as pp

import jimmy.md_lib.common

LOGGER = logging.getLogger("jimmy")


###########################################################
# wikitext parsing and conversion to markdown
###########################################################


# Prevent spaces, tabs and newlines from being stripped.
pp.ParserElement.set_default_whitespace_chars("")

# speedup: https://github.com/pyparsing/pyparsing/wiki/Performance-Tips
# - pp.ParserElement.enable_packrat() -> seems to be even slower
# - use regex instead of chaining
multiline_quote_re = re.compile(r"<<<\n([\S\s]*?)\n<<<(.*)")
link_re = re.compile(r"\[(ext|img.*?)?\[(.*?)\]\]")
list_re = re.compile(r"^([*#>]+) ", re.MULTILINE)
table_row_re = re.compile(r"\|(.*?)\|([kchf])?\n")


def dash():
    def to_md(_, t):  # noqa
        return "–" if len(t) == 2 else "—"

    return pp.Literal("-")[2, 3].set_parse_action(to_md)


def heading():
    def to_md(_, t):  # noqa
        return "#" * len(t)

    return (pp.LineStart() + pp.Literal("!")[1, 6]).set_parse_action(to_md)


def quote(source_tag, target_tag):
    """Conversion of a quoted string. I. e. with the same start and end tags."""

    def to_md(_, t):  # noqa
        return target_tag + t[0] + target_tag

    return pp.QuotedString(source_tag).set_parse_action(to_md)


def italic():
    def to_md(_, t):  # noqa
        return "*" + t[0][0] + "*"

    return pp.Regex(jimmy.md_lib.common.double_slash_re, as_group_list=True).set_parse_action(to_md)


def horizontal_line():
    return pp.Regex(jimmy.md_lib.common.horizontal_line_re).set_parse_action(lambda: "---")


def link():
    def to_md(_, t):  # noqa
        type_, content = t[0]
        match type_:
            case "img":
                prefix = "!"
            case "ext" | None:
                prefix = ""
            case _:
                LOGGER.debug(f"Unknown link type: {type_}")
                return content
        try:
            title, url = content.split("|", maxsplit=1)
        except ValueError:
            title = content
            url = content

        md_link = jimmy.md_lib.common.MarkdownLink(url=url)

        # wrap files with special characters in angle brackets
        if (
            type_ == "ext"
            and not md_link.is_web_link
            and not md_link.is_mail_link
            and urllib.parse.quote(url) != url
        ):
            url = f"<{url}>"

        if type_ == "ext" or prefix or md_link.is_web_link or md_link.is_mail_link:
            return f"{prefix}[{title}]({url})"
        # guess that it's a wikilink
        return f"{prefix}[{title}](tiddlywiki://{url})"

    return pp.Regex(link_re, as_group_list=True).set_parse_action(to_md)


def list_():
    def to_md(_, t):  # noqa
        match = t[0][0]
        spaces = (len(match) - 1) * 4
        list_character = {"*": "*", "#": "1.", ">": ">"}[match[-1]]
        return f"{' ' * spaces}{list_character} "

    return pp.Regex(list_re, as_group_list=True).set_parse_action(to_md)


def multiline_quote():
    def to_md(_, t):  # noqa
        citation = "".join(f"\n> {line}" for line in t[0][0].strip().split("\n"))
        author = f"\n> *{t[0][1].strip()}*" if t[0][1] else ""
        return citation + author

    return pp.Regex(multiline_quote_re, as_group_list=True).set_parse_action(to_md)


def table():
    def clean_cell(text: str) -> str:
        # remove unsupported directives and whitespace
        text = text.strip()
        if text in (">", "<", "~"):
            return ""
        if text.startswith(",") or text.startswith("^"):
            text = text[1:].strip()
        return text

    def to_md(_, t):  # noqa
        table_md = jimmy.md_lib.common.MarkdownTable()
        for row in t:
            content, control = row

            # The last row is a pseudo-row with a single control char:
            # https://tiddlywiki.com/static/Tables%2520in%2520WikiText.html
            is_header = False
            match control:
                case "c":
                    table_md.caption = clean_cell(content)
                    continue
                case "k":
                    continue  # ignore css classes
                case "f" | None:
                    pass  # handle as usual row
                case "h":
                    is_header = True
                case _:
                    LOGGER.debug(f"Unknown control: {control}")

            cells = [clean_cell(c) for c in content.split("|")]
            if all(c.startswith("!") for c in cells):
                is_header = True
                cells = [c[1:].strip() for c in cells]

            # new row
            if is_header:
                table_md.header_rows.append(cells)
            else:
                table_md.data_rows.append(cells)
        return table_md.create_md() + "\n"

    return pp.Regex(table_row_re, as_group_list=True)[1, ...].set_parse_action(to_md)


def wikitext_to_md(wikitext: str) -> str:
    r"""
    Main tiddlywiki wikitext to Markdown conversion function.

    >>> wikitext_to_md("Double single quotes are used for ''bold'' text")
    'Double single quotes are used for **bold** text'
    >>> wikitext_to_md("//italic text://")
    '*italic text:*'
    >>> wikitext_to_md("from http://127.0.0.1/MyApp to default http://127.0.0.1/.")
    'from http://127.0.0.1/MyApp to default http://127.0.0.1/.'
    >>> wikitext_to_md("! level 1 heading!\n!!!!!! level 6! heading")
    '# level 1 heading!\n###### level 6! heading'
    >>> wikitext_to_md("<<<\nThis is a block quoted paragraph\nwritten in English\n<<<")
    '\n> This is a block quoted paragraph\n> written in English'
    >>> wikitext_to_md("<<<\nComputers are like a bicycle for our minds\n<<< S. Jobs")
    '\n> Computers are like a bicycle for our minds\n> *S. Jobs*'
    >>> wikitext_to_md("> Quoted text\n> Another line of quoted text")
    '> Quoted text\n> Another line of quoted text'
    >>> wikitext_to_md("* -- n-dash\n* --- m-dash --- example\n----")
    '* – n-dash\n* — m-dash — example\n---'
    >>> wikitext_to_md("----\n---")
    '---\n---'
    >>> wikitext_to_md("[img[Motovun Jack.jpg]]")
    '![Motovun Jack.jpg](Motovun Jack.jpg)'
    >>> wikitext_to_md("[img[https://tiddlywiki.com/favicon.ico]]")
    '![https://tiddlywiki.com/favicon.ico](https://tiddlywiki.com/favicon.ico)'
    >>> wikitext_to_md("[img[An explanatory tooltip|Motovun Jack.jpg]]")
    '![An explanatory tooltip](Motovun Jack.jpg)'
    >>> wikitext_to_md("abc [img[a|b.jpg]] def")
    'abc ![a](b.jpg) def'
    >>> wikitext_to_md("[img width=32 class='tc-image' [Motovun Jack.jpg]]")
    '![Motovun Jack.jpg](Motovun Jack.jpg)'
    >>> wikitext_to_md("link to [[Tiddler Title]]")
    'link to [Tiddler Title](tiddlywiki://Tiddler Title)'
    >>> wikitext_to_md("[[Displayed Link Title|Tiddler Title]]")
    '[Displayed Link Title](tiddlywiki://Tiddler Title)'
    >>> wikitext_to_md("abc [[TW5|https://tiddlywiki.com/]]")
    'abc [TW5](https://tiddlywiki.com/)'
    >>> wikitext_to_md("[[Mail me|mailto:me@where.net]] def")
    '[Mail me](mailto:me@where.net) def'
    >>> wikitext_to_md("[[mailto:me@where.net]] def")
    '[mailto:me@where.net](mailto:me@where.net) def'
    >>> wikitext_to_md("[[Open file|file:///c:/users/me/index.html]]")
    '[Open file](file:///c:/users/me/index.html)'
    >>> wikitext_to_md("[ext[Open file|index.html]]")
    '[Open file](index.html)'
    >>> wikitext_to_md("abc [ext[Open file|./index.html]]")
    'abc [Open file](./index.html)'
    >>> wikitext_to_md("[ext[Open file|../README.md]] def")
    '[Open file](../README.md) def'
    >>> wikitext_to_md("[ext[Open file|../README Space.md]] def")
    '[Open file](<../README Space.md>) def'
    >>> wikitext_to_md("[ext[Open file|c:\\users\\me\\index.html]]")
    '[Open file](<c:\\users\\me\\index.html>)'
    >>> wikitext_to_md("[ext[https://www.bvb.de/]]")
    '[https://www.bvb.de/](https://www.bvb.de/)'
    >>> wikitext_to_md("text1 [[title 1|link 1]] text2 [[link2]] text3")
    'text1 [title 1](tiddlywiki://link 1) text2 [link2](tiddlywiki://link2) text3'
    >>> wikitext_to_md("`[]`, [[Links|Links]], [[Filters|Filters]]")
    '`[]`, [Links](tiddlywiki://Links), [Filters](tiddlywiki://Filters)'
    >>> wikitext_to_md("* First item\n* Second item\n** Subitem\n* Third list item")
    '* First item\n* Second item\n    * Subitem\n* Third list item'
    >>> wikitext_to_md("# Step 1\n# Step 2\n## Step2.1\n# Step 3")
    '1. Step 1\n1. Step 2\n    1. Step2.1\n1. Step 3'
    >>> wikitext_to_md("* Do today\n*# Eat\n* To do\n*# This\n*# That\n*## Other")
    '* Do today\n    1. Eat\n* To do\n    1. This\n    1. That\n        1. Other'
    >>> wikitext_to_md("* One\n** Two\n**> A quote\n**> Another quote\n* List Three")
    '* One\n    * Two\n        > A quote\n        > Another quote\n* List Three'
    >>> wikitext_to_md("|!Cell1 |!Cell2 |\n|Cell3 |Cell4 |\n")
    '| Cell1 | Cell2 |\n| --- | --- |\n| Cell3 | Cell4 |\n'
    >>> wikitext_to_md("|C1 |C2 |C3 |\n|C4 |C5 |<|\n|C6 |~|C7 |\n|>|C8 |C9 |\n")
    '| C1 | C2 | C3 |\n| C4 | C5 |  |\n| C6 |  | C7 |\n|  | C8 | C9 |\n'
    >>> wikitext_to_md("|^t l |^t c |^ t r|\n|m l |m c | m r|\n|,b l |, b c |,b r|\n")
    '| t l | t c | t r |\n| m l | m c | m r |\n| b l | b c | b r |\n'
    >>> wikitext_to_md("|cls|k\n|caption |c\n|C1 |C2|\n|C3|C4 |\n|H1|H2|h\n|F1|F2|f\n")
    'caption\n\n| H1 | H2 |\n| --- | --- |\n| C1 | C2 |\n| C3 | C4 |\n| F1 | F2 |\n'
    >>> wikitext_to_md("- ''modifier''\n- __underlined__")
    '- **modifier**\n- ++underlined++'
    >>> wikitext_to_md("|C1 |''modifier''|\n")
    '| C1 | **modifier** |\n'
    """
    wikitext_markup = (
        # basic formatting:
        # https://tiddlywiki.com/static/Formatting%2520in%2520WikiText.html
        quote("''", "**")
        | quote("__", "++")
        | quote("^^", "^")
        | quote(",,", "~")
        # | quote("~~", "~~")
        | quote("@@", "==")
        | italic()
        # https://tiddlywiki.com/static/Horizontal%2520Rules%2520in%2520WikiText.html
        | horizontal_line()
        # inline code and code blocks
        # https://tiddlywiki.com/static/Code%2520Blocks%2520in%2520WikiText.html
        # | quote("`", "`")
        # dashes: https://tiddlywiki.com/static/Dashes%2520in%2520WikiText.html
        | dash()
        # headings: https://tiddlywiki.com/static/Headings%2520in%2520WikiText.html
        | heading()
        # (external) links: https://tiddlywiki.com/static/Linking%2520in%2520WikiText.html
        # images: https://tiddlywiki.com/static/Images%2520in%2520WikiText.html
        | link()
        # https://tiddlywiki.com/static/Lists%2520in%2520WikiText.html
        | list_()
    )
    # TODO: Why does "table" overwrite other rules when executes in the same run?
    wikitext_complex = (
        # block quote:
        # https://tiddlywiki.com/static/Block%2520Quotes%2520in%2520WikiText.html
        multiline_quote()
        # https://tiddlywiki.com/static/Tables%2520in%2520WikiText.html
        | table()
    )
    return wikitext_complex.transform_string(wikitext_markup.transform_string(wikitext))
