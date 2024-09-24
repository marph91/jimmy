"""Convert TiddlyWiki notes to the intermediate format."""

import datetime as dt
from pathlib import Path
import json
import re
import string

import pyparsing as pp

import converter
import intermediate_format as imf


###########################################################
# wikitext parsing and conversion to markdown
###########################################################


# Prevent spaces, tabs and newlines from being stripped.
pp.ParserElement.set_default_whitespace_chars("")

# speedup: https://github.com/pyparsing/pyparsing/wiki/Performance-Tips
# - pp.ParserElement.enablePackrat() -> seems to be even slower
# - use regex -> TODO
multiline_quote_re = re.compile(r"<<<\n([\S\s]*?)\n<<<(.*)")


def single(source_tag, target_tag, start_of_line=False):
    """Conversion of a single character."""
    if start_of_line:
        return (pp.LineStart() + pp.Literal(source_tag)).setParseAction(
            lambda: target_tag
        )
    return pp.Literal(source_tag).setParseAction(lambda: target_tag)


def quote(source_tag, target_tag):
    """Conversion of a quoted string. I. e. with the same start and end tags."""

    def to_md(_, t):  # noqa
        return target_tag + t[0] + target_tag

    return pp.QuotedString(source_tag).setParseAction(to_md)


def horizontal_line():
    return (pp.LineStart() + pp.Literal("-")[3, ...] + pp.LineEnd()).setParseAction(
        lambda: "---\n"
    )


def image():
    def to_md(_, t):  # noqa
        text = t[0][t[0].find("[") + 1 :]
        try:
            title, url = text.split("|", maxsplit=1)
        except ValueError:
            title = ""
            url = text
        return f"![{title}]({url})"

    return pp.QuotedString("[img", endQuoteChar="]]").setParseAction(to_md)


def link():
    def to_md(_, t):  # noqa
        text = t[0][t[0].find("[") + 1 :]
        try:
            title, url = text.split("|", maxsplit=1)
        except ValueError:
            title = ""
            url = text
        return f"[{title}]({url})"

    return pp.QuotedString("[[", endQuoteChar="]]").setParseAction(to_md)


def external_link():
    def to_md(_, t):  # noqa
        text = t[0][t[0].find("[") + 1 :]
        try:
            title, url = text.split("|", maxsplit=1)
        except ValueError:
            title = ""
            url = text
        return f"[{title}]({url})"

    return pp.QuotedString("[ext", endQuoteChar="]]").setParseAction(to_md)


def list_():
    def to_md(_, t):  # noqa
        spaces = (len(t[-1]) - 1) * 4
        list_character = {"*": "*", "#": "1.", ">": ">"}[t[-1][-1]]
        return f"{' ' * spaces}{list_character}"

    return (pp.LineStart() + pp.Word("*#>")).setParseAction(to_md)


def multiline_quote():
    def to_md(_, t):  # noqa
        citation = "".join(f"\n> {line}" for line in t[0][0].strip().split("\n"))
        author = f"\n> *{t[0][1].strip()}*" if t[0][1] else ""
        return citation + author

    return pp.Regex(multiline_quote_re, as_group_list=True).setParseAction(to_md)


def table():
    table_row = (
        pp.LineStart()
        + pp.Literal("|")
        + (pp.Word(string.printable, exclude_chars="|\n") + pp.Literal("|"))[1, ...]
        + pp.Char("kchf")[0, 1]
        + pp.LineEnd()
    )

    def clean_cell(text: str) -> str:
        # remove unsupported directives and whitespace
        text = text.strip()
        if text in (">", "<", "~"):
            return ""
        if text.startswith(",") or text.startswith("^"):
            text = text[1:].strip()
        return text

    def to_md(_, t):  # noqa
        table_md: list[str] = []
        current_row: list[str] = []
        is_header = False
        caption = ""
        for index, value in enumerate(t):
            if value == "|":
                continue
            if value == "\n":
                if t[index - 1] != "|":
                    # The last row is a pseudo-row with a single control char:
                    # https://tiddlywiki.com/static/Tables%2520in%2520WikiText.html
                    control = current_row.pop(-1)
                    match control:
                        case "c":
                            caption = current_row.pop() + "\n\n"
                            current_row = []
                            is_header = False
                            continue
                        case "c" | "k":
                            # ignore css classes
                            current_row = []
                            is_header = False
                            continue
                        case "f":
                            pass  # handle footer as usual row
                        case "h":
                            is_header = True
                        case _:
                            print(f"Unknown control character {control}")

                # new row
                if is_header and "| --- |" not in table_md:
                    # header can only be the first row
                    table_md.insert(0, "| " + " | ".join(current_row) + " |")
                    separator = ["---"] * len(current_row)
                    table_md.insert(1, "| " + " | ".join(separator) + " |")
                else:
                    table_md.append("| " + " | ".join(current_row) + " |")
                current_row = []
                is_header = False
            else:
                if value.startswith("!"):
                    # header row
                    is_header = True
                    current_row.append(clean_cell(value[1:]))
                else:
                    current_row.append(clean_cell(value))
        return caption + "\n".join(table_md) + "\n"

    return (table_row[1, ...]).setParseAction(to_md)


def wikitext_to_md(wikitext: str) -> str:
    r"""
    Main tiddlywiki wikitext to Markdown conversion function.

    TODO:
    # >>> wikitext_to_md("from http://127.0.0.1/MyApp to default http://127.0.0.1/.")
    # 'from http://127.0.0.1/MyApp to default http://127.0.0.1/.'

    >>> wikitext_to_md("Double single quotes are used for ''bold'' text")
    'Double single quotes are used for **bold** text'
    >>> wikitext_to_md("! level 1 heading!\n!! level 2! heading")
    '# level 1 heading!\n## level 2! heading'
    >>> wikitext_to_md("<<<\nThis is a block quoted paragraph\nwritten in English\n<<<")
    '\n> This is a block quoted paragraph\n> written in English'
    >>> wikitext_to_md("<<<\nComputers are like a bicycle for our minds\n<<< S. Jobs")
    '\n> Computers are like a bicycle for our minds\n> *S. Jobs*'
    >>> wikitext_to_md("> Quoted text\n> Another line of quoted text")
    '> Quoted text\n> Another line of quoted text'
    >>> wikitext_to_md("* -- n-dash\n* --- m-dash --- example\n----")
    '* – n-dash\n* — m-dash — example\n---\n'
    >>> wikitext_to_md("[img[Motovun Jack.jpg]]")
    '![](Motovun Jack.jpg)'
    >>> wikitext_to_md("[img[https://tiddlywiki.com/favicon.ico]]")
    '![](https://tiddlywiki.com/favicon.ico)'
    >>> wikitext_to_md("[img[An explanatory tooltip|Motovun Jack.jpg]]")
    '![An explanatory tooltip](Motovun Jack.jpg)'
    >>> wikitext_to_md("abc [img[a|b.jpg]] def")
    'abc ![a](b.jpg) def'
    >>> wikitext_to_md("[img width=32 class='tc-image' [Motovun Jack.jpg]]")
    '![](Motovun Jack.jpg)'
    >>> wikitext_to_md("link to [[Tiddler Title]]")
    'link to [](Tiddler Title)'
    >>> wikitext_to_md("[[Displayed Link Title|Tiddler Title]]")
    '[Displayed Link Title](Tiddler Title)'
    >>> wikitext_to_md("abc [[TW5|https://tiddlywiki.com/]]")
    'abc [TW5](https://tiddlywiki.com/)'
    >>> wikitext_to_md("[[Mail me|mailto:me@where.net]] def")
    '[Mail me](mailto:me@where.net) def'
    >>> wikitext_to_md("[[Open file|file:///c:/users/me/index.html]]")
    '[Open file](file:///c:/users/me/index.html)'
    >>> wikitext_to_md("[ext[Open file|index.html]]")
    '[Open file](index.html)'
    >>> wikitext_to_md("abc [ext[Open file|./index.html]]")
    'abc [Open file](./index.html)'
    >>> wikitext_to_md("[ext[Open file|../README.md]] def")
    '[Open file](../README.md) def'
    >>> wikitext_to_md("[ext[Open file|c:\\users\\me\\index.html]]")
    '[Open file](c:\\users\\me\\index.html)'
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
    """
    wikitext_markup = (
        # basic formatting:
        # https://tiddlywiki.com/static/Formatting%2520in%2520WikiText.html
        quote("''", "**")
        | quote("//", "*")
        | quote("__", "++")
        | quote("^^", "^")
        | quote(",,", "~")
        # | quote("~~", "~~")
        | quote("@@", "**")  # highlight -> bold
        # https://tiddlywiki.com/static/Horizontal%2520Rules%2520in%2520WikiText.html
        | horizontal_line()
        # inline code and code blocks
        # https://tiddlywiki.com/static/Code%2520Blocks%2520in%2520WikiText.html
        # | quote("`", "`")
        # dashes: https://tiddlywiki.com/static/Dashes%2520in%2520WikiText.html
        | single("---", "—")
        | single("--", "–")
        # headings: https://tiddlywiki.com/static/Headings%2520in%2520WikiText.html
        | single("!" * 6, "#" * 6, start_of_line=True)
        | single("!" * 5, "#" * 5, start_of_line=True)
        | single("!" * 4, "#" * 4, start_of_line=True)
        | single("!" * 3, "#" * 3, start_of_line=True)
        | single("!" * 2, "#" * 2, start_of_line=True)
        | single("!", "#" * 1, start_of_line=True)
        # https://tiddlywiki.com/static/Images%2520in%2520WikiText.html
        | image()
        # https://tiddlywiki.com/static/Linking%2520in%2520WikiText.html
        | link()
        | external_link()
        # https://tiddlywiki.com/static/Lists%2520in%2520WikiText.html
        | list_()
        # block quote:
        # https://tiddlywiki.com/static/Block%2520Quotes%2520in%2520WikiText.html
        | multiline_quote()
        # https://tiddlywiki.com/static/Tables%2520in%2520WikiText.html
        | table()
    )
    return wikitext_markup.transformString(wikitext)


###########################################################
# metadata and intermadiate format
###########################################################


def tiddlywiki_to_datetime(tiddlywiki_time: str) -> dt.datetime:
    """Format: https://tiddlywiki.com/static/DateFormat.html"""
    return dt.datetime.strptime(tiddlywiki_time, "%Y%m%d%H%M%S%f")


def split_tags(tag_string: str) -> list[str]:
    """
    Tags are space separated. Tags with spaces are surrounded by double brackets.

    >>> split_tags("tag1 tag2 tag3 [[tag with spaces]]")
    ['tag1', 'tag2', 'tag3', 'tag with spaces']
    >>> split_tags("[[tag with spaces]]")
    ['tag with spaces']
    >>> split_tags("tag1 tag2 tag3")
    ['tag1', 'tag2', 'tag3']
    >>> split_tags("")
    []
    """
    if not tag_string.strip():
        return []
    space_splitted = tag_string.split(" ")
    final_tags = []
    space_separated_tag = ""
    for part in space_splitted:
        if space_separated_tag:
            if part.endswith("]]"):
                space_separated_tag += " " + part[:-2]
                final_tags.append(space_separated_tag)
                space_separated_tag = ""
            else:
                space_separated_tag += " " + part
        elif part.startswith("[["):
            space_separated_tag = part[2:]
        else:
            final_tags.append(part)
    return final_tags


class Converter(converter.BaseConverter):
    accepted_extensions = [".json"]

    def convert(self, file_or_folder: Path):
        file_dict = json.loads(Path(file_or_folder).read_text(encoding="utf-8"))
        for note_tiddlywiki in file_dict:
            title = note_tiddlywiki["title"]
            self.logger.debug(f'Converting note "{title}"')
            note_imf = imf.Note(
                title,
                wikitext_to_md(note_tiddlywiki.get("text", "")),
                author=note_tiddlywiki.get("creator"),
                source_application=self.format,
                # Tags don't have a separate id. Just use the name as id.
                tags=[
                    imf.Tag(tag) for tag in split_tags(note_tiddlywiki.get("tags", ""))
                ],
            )
            if "created" in note_tiddlywiki:
                note_imf.created = tiddlywiki_to_datetime(note_tiddlywiki["created"])
            if "modified" in note_tiddlywiki:
                note_imf.updated = tiddlywiki_to_datetime(note_tiddlywiki["modified"])
            if any(t.reference_id.startswith("$:/tags/") for t in note_imf.tags):
                continue  # skip notes with special tags
            self.root_notebook.child_notes.append(note_imf)
