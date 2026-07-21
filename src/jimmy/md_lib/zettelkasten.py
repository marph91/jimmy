"""Convert Zettelkasten (zkn3) bbcode to Markdown."""

import re

import pyparsing as pp

import jimmy.md_lib.links
import jimmy.md_lib.tables

# Prevent spaces, tabs and newlines from being stripped.
pp.ParserElement.set_default_whitespace_chars("")


colored_re = re.compile(r"\[h .*\](.*?)\[\/h\]")
internal_link_re = re.compile(r"\[z (\d+)\](.*?)\[\/z\]")
table_re = re.compile(r"\[table\](\[tc\](.*?)\[\/tc\])?([\S\s]*?)\[\/table\]")
# hacky, but works for now
list_re = re.compile(r"\[([ln])\]\[\*\](.*?)\[\/\*\]\[\/[ln]\]")


bbcode_markup = pp.Forward()


def tag(source_tag, target_tag, replace_first_only=False):
    """Conversion of a quoted string. I. e. with the same start and end tags."""

    def to_md(tokens):
        if replace_first_only:
            return target_tag + bbcode_markup.transform_string(tokens[0])
        return target_tag + bbcode_markup.transform_string(tokens[0]) + target_tag

    return pp.QuotedString(f"[{source_tag}]", end_quote_char=f"[/{source_tag}]").set_parse_action(
        to_md
    )


def newline():
    return pp.Literal("[br]").set_parse_action(lambda: "\n")


def colored():
    # colored -> highlight
    def to_md(tokens):
        return "==" + bbcode_markup.transform_string(tokens[0][0]) + "=="

    return pp.Regex(colored_re, as_group_list=True).set_parse_action(to_md)


def code_block():
    def to_md(tokens):
        # only transform newlines in code blocks
        return f"\n```\n{newline().transform_string(tokens[0])}\n```"

    return pp.QuotedString("[code]", end_quote_char="[/code]", multiline=True).set_parse_action(
        to_md
    )


def list_():
    def to_md(tokens):
        type_, content = tokens[0]
        list_character = {"l": "*", "n": "1."}[type_]

        list_items = []
        for list_item in content.split("[/*][*]"):
            list_items.append(bbcode_markup.transform_string(list_item))

        return f"{list_character} " + f"\n{list_character} ".join(list_items) + "\n"

    return pp.Regex(list_re, as_group_list=True).set_parse_action(to_md)


def image():
    def to_md(tokens):
        return jimmy.md_lib.links.make_link(tokens[0], tokens[0], is_image=True)

    return pp.QuotedString("[img]", end_quote_char="[/img]").set_parse_action(to_md)


def internal_link():
    def to_md(tokens):
        id_, title = tokens[0]
        title = bbcode_markup.transform_string(title)
        return f"[{title}](note://{id_})"

    return pp.Regex(internal_link_re, as_group_list=True).set_parse_action(to_md)


def table():
    def to_md(tokens):
        _, caption, content = tokens[0]

        table_md = jimmy.md_lib.tables.MarkdownTable()
        if caption is not None:
            table_md.caption = caption

        for line in content.split("[br]"):
            if not line.strip():
                continue
            if "^" in line:
                table_md.header_rows.append(
                    [bbcode_markup.transform_string(cell) for cell in line.split("^")]
                )
            else:
                table_md.data_rows.append(
                    [bbcode_markup.transform_string(cell) for cell in line.split("|")]
                )
        return table_md.create_md()

    return pp.Regex(table_re, as_group_list=True).set_parse_action(to_md)


bbcode_markup <<= (
    # more specific markup first
    list_()
    | code_block()
    | table()
    #
    | image()
    | internal_link()
    | newline()
    # text formatting
    | tag("f", "**")
    | tag("k", "*")
    | tag("u", "++")
    | tag("d", "~~")
    | tag("qm", '"')
    | tag("sub", "~")
    | tag("sup", "^")
    | colored()
    # left, right aligned, centered, justified - not supported
    | tag("al", "")
    | tag("ar", "")
    | tag("c", "")
    | tag("ab", "")
    #
    | tag("h1", "# ", replace_first_only=True)
    | tag("h2", "## ", replace_first_only=True)
    | tag("h3", "### ", replace_first_only=True)
    | tag("h4", "#### ", replace_first_only=True)
    | tag("h5", "##### ", replace_first_only=True)
    | tag("h6", "###### ", replace_first_only=True)
    | tag("q", "> ", replace_first_only=True)
)


def bbcode_to_md(bbcode: str) -> str:
    r"""
    Main bbcode to Markdown conversion function.

    # hyperlinks are markdown already

    >>> bbcode_to_md("[f]fett[/f]")
    '**fett**'
    >>> bbcode_to_md("das ist [d]durchgestrichener[/d] text")
    'das ist ~~durchgestrichener~~ text'
    >>> bbcode_to_md("[h #ffff00]colored[/h] text")
    '==colored== text'
    >>> bbcode_to_md("[h3]heading 3[/h3]")
    '### heading 3'
    >>> bbcode_to_md("some[br]li nes[br]he re")
    'some\nli nes\nhe re'
    >>> bbcode_to_md("[q]single line quote[/q]")
    '> single line quote'
    >>> bbcode_to_md("disappearing [al]tag[/al]")
    'disappearing tag'
    >>> bbcode_to_md("[code]some code[/code]")
    '\n```\nsome code\n```'
    >>> bbcode_to_md("[code]long[br]code block[/code]")
    '\n```\nlong\ncode block\n```'
    >>> bbcode_to_md("[img]some image.png[/img]")
    '![some image.png](some image.png)'
    >>> bbcode_to_md("link [z 3]zu Zettel 3[/z]")
    'link [zu Zettel 3](note://3)'
    >>> bbcode_to_md("[table][tc]Test Table[/tc][br]h 1^h 2^h3[br]d1 |d 2 |d3[/table]")
    'Test Table\n\n| h 1 | h 2 | h3 |\n| --- | --- | --- |\n| d1  | d 2  | d3 |'
    >>> bbcode_to_md("[table]h 1^h 2^h3[br][f]fett[/f] |d 2 |d3[/table]")
    '| h 1 | h 2 | h3 |\n| --- | --- | --- |\n| **fett**  | d 2  | d3 |'
    >>> bbcode_to_md("[l][*]Here an item[/*][*]Other [d]item[/d]![/*][/l]")
    '* Here an item\n* Other ~~item~~!\n'
    >>> bbcode_to_md("[n][*]Numbered item[/*][*]Other numbered item![/*][/n]")
    '1. Numbered item\n1. Other numbered item!\n'
    """
    return bbcode_markup.transform_string(bbcode)
