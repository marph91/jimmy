"""Convert Zim Wiki to Markdown."""

from pathlib import Path
import re

import pyparsing as pp

import jimmy.md_lib.common
import jimmy.md_lib.links

# Prevent spaces, tabs and newlines from being stripped.
pp.ParserElement.set_default_whitespace_chars("")


heading_re = re.compile(r"(={1,6}) (.*?) ={1,6}")
checklist_re = re.compile(r"^( *)\[([ <>*x])\] ", re.MULTILINE)


def zim_to_md(zim_text: str, resource_path: Path = Path(".")) -> str:
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
    >>> zim_to_md("**__highlighted and bold__**")
    '**==highlighted and bold==**'
    >>> zim_to_md("'''\nsome code\nblock\n'''")
    '```\nsome code\nblock\n```'
    >>> zim_to_md("[ ] unchecked\n[x] not done")
    '- [ ] unchecked\n- [x] not done'
    >>> zim_to_md("[ ] u\n    [>] np\n    [*] nd\n[x] nd")
    '- [ ] u\n    - [ ] np\n    - [x] nd\n- [x] nd'
    >>> zim_to_md("* lvl1\n\t* lvl2\n\t* lvl2\n* lvl1")
    '* lvl1\n    * lvl2\n    * lvl2\n* lvl1'
    >>> zim_to_md("{{./image.png}}")
    '![image.png](image.png)'
    >>> zim_to_md("{{./image.png?width=600}}")
    '![image.png](image.png)'
    >>> zim_to_md("[[#heading3|heading3]]")
    '[heading3](#heading3)'
    >>> zim_to_md("[[https://www.bvb.de/|TITLE ''monospace'']]")
    '[TITLE `monospace`](https://www.bvb.de/)'
    >>> zim_to_md("[[./0.mp3]]")
    '[./0.mp3](0.mp3)'
    """
    zim_markup = pp.Forward()

    def quote(source_tag, target_tag):
        """Conversion of a quoted string. I. e. with the same start and end tags."""

        def to_md(tokens):
            return target_tag + zim_markup.transform_string(tokens[0]) + target_tag

        return pp.QuotedString(source_tag).set_parse_action(to_md)

    def subscript():
        def to_md(tokens):
            return "~" + zim_markup.transform_string(tokens[0]) + "~"

        return pp.QuotedString("_{", end_quote_char="}").set_parse_action(to_md)

    def superscript():
        def to_md(tokens):
            return "^" + zim_markup.transform_string(tokens[0]) + "^"

        return pp.QuotedString("^{", end_quote_char="}").set_parse_action(to_md)

    def highlight():
        def to_md(tokens):
            return "==" + zim_markup.transform_string(tokens[0]) + "=="

        return pp.QuotedString("__").set_parse_action(to_md)

    def italic():
        def to_md(tokens):
            return "*" + zim_markup.transform_string(tokens[0][0]) + "*"

        return pp.Regex(jimmy.md_lib.common.double_slash_re, as_group_list=True).set_parse_action(
            to_md
        )

    def horizontal_line():
        return pp.Regex(jimmy.md_lib.common.horizontal_line_re).set_parse_action(lambda: "\n---\n")

    def heading():
        def to_md(tokens):
            return "#" * (7 - len(tokens[0][0])) + " " + zim_markup.transform_string(tokens[0][1])

        return pp.Regex(heading_re, as_group_list=True).set_parse_action(to_md)

    def checklist():
        def to_md(tokens):
            list_char = "x" if tokens[0][1] in ("*", "x") else " "
            return f"{tokens[0][0]}- [{list_char}] "

        return pp.Regex(checklist_re, as_group_list=True).set_parse_action(to_md)

    def image(resource_path: Path):
        def to_md(tokens):
            image_path = Path(tokens[0].split("?")[0])  # strip queries like "?width=600px"
            image_path_resolved = resolve_resource(resource_path, image_path)
            return jimmy.md_lib.links.make_link(image_path.name, image_path_resolved, is_image=True)

        return pp.QuotedString("{{", end_quote_char="}}").set_parse_action(to_md)

    def link(resource_path: Path):
        # https://zim-wiki.org/manual/Help/Links.html
        def to_md(tokens):
            t_splitted = tokens[0].rsplit("|", maxsplit=1)
            url = t_splitted[0]

            # Links that start with a '+' are resolved as sub-pages below the current page
            url = url.lstrip("+")
            title = url if len(t_splitted) < 2 else zim_markup.transform_string(t_splitted[1])

            if any(url.startswith(scheme) for scheme in jimmy.md_lib.common.web_schemes):
                # URLs are recognized because they start with e.g. "https://" or "mailto:".
                pass
            elif "/" in url:
                # Links containing a '/' are considered links to external files
                url = resolve_resource(resource_path, Path(url))
            return jimmy.md_lib.links.make_link(title, url)

        return pp.QuotedString("[[", end_quote_char="]]").set_parse_action(to_md)

    def resolve_resource(resource_path: Path, url: Path) -> str:
        # relative resources are stored in a folder named like the note
        # example:
        # - note.md
        # - note/image.png
        if Path.home() in Path(url).expanduser().parents:
            # add "file://" protocol to external files
            # https://stackoverflow.com/a/72117102/7410886
            return Path(url).expanduser().as_uri()
        return str(url if Path(url).is_absolute() else resource_path / url)

    zim_markup <<= (
        pp.Literal("'''").set_parse_action(lambda: "```")
        # text formatting
        | quote("''", "`")
        | highlight()
        | italic()
        | subscript()
        | superscript()
        #
        | link(resource_path)
        | image(resource_path)
        | horizontal_line()
        | heading()
        | checklist()
    )

    # str.translate() seems to be fastest, but works only on single characters.
    # https://stackoverflow.com/a/8958372
    zim_text = zim_text.expandtabs(4)
    return zim_markup.transform_string(zim_text)
