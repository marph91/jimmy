"""Common Markdown functions."""

import dataclasses
import logging
from pathlib import Path
import re

from bs4 import BeautifulSoup
import markdown
from markdown.treeprocessors import Treeprocessor
from markdown.extensions import Extension
import pydantic
import pypandoc

import jimmy.md_lib.html_filter


LOGGER = logging.getLogger("jimmy")


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


@pydantic.dataclasses.dataclass
class MarkdownTable:
    """Construct a Markdown table from lists."""

    header_rows: list[list[str]] = dataclasses.field(default_factory=list)
    data_rows: list[list[str]] = dataclasses.field(default_factory=list)
    caption: str = ""

    def create_md(self) -> str:
        # column sanity check
        columns = [len(row) for row in self.header_rows + self.data_rows]
        if len(set(columns)) not in (0, 1):
            LOGGER.warning(f"Amount of columns differs: {columns}")

        def create_md_row(cells: list[str]) -> str:
            return "| " + " | ".join(cells) + " |"

        rows_md = []
        for row in self.header_rows:
            rows_md.append(create_md_row(row))
        if self.header_rows:
            separator = ["---"] * len(self.header_rows[0])
            rows_md.append(create_md_row(separator))
        for row in self.data_rows:
            rows_md.append(create_md_row(row))

        caption = self.caption + "\n\n" if self.caption else ""
        return caption + "\n".join(rows_md)


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


@pydantic.dataclasses.dataclass
class MarkdownLink:
    """
    Represents a markdown link:
    - link: https://www.markdownguide.org/basic-syntax/#links
    - image: https://www.markdownguide.org/basic-syntax/#images-1
    """

    # TODO: doctest

    text: str = ""
    url: str = ""
    title: str = ""
    is_image: bool = False

    @property
    def is_web_link(self) -> bool:
        return any(self.url.startswith(f"{protocol}://") for protocol in web_schemes)

    @property
    def is_mail_link(self) -> bool:
        return self.url.startswith("mailto:")

    def __str__(self) -> str:
        prefix = "!" if self.is_image else ""
        title = "" if not self.title else f' "{self.title}"'
        return f"{prefix}[{self.text}]({self.url}{title})"

    def reformat(self) -> str:
        if not self.url:
            return f"<{self.text}>"
        if self.is_web_link and self.text == self.url:
            return f"<{self.url}>"
        prefix = "!" if self.is_image else ""
        title = "" if not self.title else f' "{self.title}"'
        return f"{prefix}[{self.text}]({self.url}{title})"


class LinkExtractor(Treeprocessor):
    # We need to unescape manually. Reference: "UnescapeTreeprocessor"
    # https://github.com/Python-Markdown/markdown/blob/3.6/markdown/treeprocessors.py#L454
    RE = re.compile(rf"{markdown.util.STX}(\d+){markdown.util.ETX}")

    def _unescape(self, m: re.Match[str]) -> str:
        return "\\" + chr(int(m.group(1)))

    def unescape(self, text: str) -> str:
        return self.RE.sub(self._unescape, text)

    def run(self, root):
        # pylint: disable=no-member
        # TODO: Find a better way.
        self.md.images = []
        self.md.links = []
        for image in root.findall(".//img"):
            self.md.images.append(
                MarkdownLink(
                    self.unescape(image.get("alt", "")),
                    image.get("src", ""),
                    image.get("title", ""),
                    is_image=True,
                )
            )
        for link in root.findall(".//a"):
            url = link.get("href", "")
            # TODO: This is not robust against titles with quotation marks.
            if (title := link.get("title", "")) and not url:
                url = title  # don't add a title if there is no url
                title = ""
            text = "" if link.text is None else link.text
            self.md.links.append(MarkdownLink(text, url, title))


class LinkExtractorExtension(Extension):
    def extendMarkdown(self, md):  # noqa: N802
        link_extension = LinkExtractor(md)
        md.treeprocessors.register(link_extension, "link_extension", 15)


MD = markdown.Markdown(extensions=[LinkExtractorExtension()])


def get_markdown_links(text: str) -> list[MarkdownLink]:
    # ruff: noqa: E501
    # doctest has too long lines
    r"""
    >>> get_markdown_links("![](image.png)")
    [MarkdownLink(text='', url='image.png', title='', is_image=True)]
    >>> get_markdown_links("![abc](image (1).png)")
    [MarkdownLink(text='abc', url='image (1).png', title='', is_image=True)]
    >>> get_markdown_links("[mul](tiple) [links](...)") # doctest: +NORMALIZE_WHITESPACE
    [MarkdownLink(text='mul', url='tiple', title='', is_image=False),
     MarkdownLink(text='links', url='...', title='', is_image=False)]
    >>> get_markdown_links("![desc \\[reference\\]](Image.png){#fig:leanCycle}")
    [MarkdownLink(text='desc \\[reference\\]', url='Image.png', title='', is_image=True)]
    >>> get_markdown_links('[link](internal "Example Title")')
    [MarkdownLink(text='link', url='internal', title='Example Title', is_image=False)]
    >>> get_markdown_links('[link](#internal)')
    [MarkdownLink(text='link', url='#internal', title='', is_image=False)]
    >>> get_markdown_links('[link](:/custom)')
    [MarkdownLink(text='link', url=':/custom', title='', is_image=False)]
    >>> get_markdown_links('[weblink](https://duckduckgo.com)')
    [MarkdownLink(text='weblink', url='https://duckduckgo.com', title='', is_image=False)]
    """
    # Based on: https://stackoverflow.com/a/29280824/7410886
    # pylint: disable=no-member
    MD.convert(text)
    try:
        md_images = [*MD.images]  # new list, because it gets cleared
        MD.images.clear()
    except AttributeError:
        md_images = []
    try:
        md_links = [*MD.links]
        MD.links.clear()
    except AttributeError:
        md_links = []
    return md_images + md_links


WIKILINK_LINK_REGEX = re.compile(r"(!)?\[\[(.+?)(?:\|(.+?))?\]\]")


def get_wikilink_links(text: str) -> list:
    return WIKILINK_LINK_REGEX.findall(text)


def get_inline_tags(text: str, start_characters: list[str]) -> list[str]:
    """
    >>> get_inline_tags("# header", ["#"])
    []
    >>> get_inline_tags("### h3", ["#"])
    []
    >>> get_inline_tags("#tag", ["#"])
    ['tag']
    >>> get_inline_tags("#tag abc", ["#"])
    ['tag']
    >>> sorted(get_inline_tags("#tag @abc", ["#", "@"]))
    ['abc', 'tag']
    """
    # TODO: can possibly be combined with todoist.split_labels()
    tags = set()
    for word in text.split():
        if (
            any(word.startswith(char) for char in start_characters)
            and len(word) > 1
            # exclude words like "###"
            and any(char not in start_characters for char in word)
        ):
            tags.add(word[1:])
    return list(tags)


# TODO:
# - "csljson" https://github.com/citation-style-language/schema
# - "dokuwiki" https://de.wikipedia.org/wiki/DokuWiki
# - Emacs Muse, Emacs org
# - "fb2" https://en.wikipedia.org/wiki/FictionBook
# - "jats" https://en.wikipedia.org/wiki/Journal_Article_Tag_Suite
#   - "bits" https://jats.nlm.nih.gov/extensions/bits/
# - json

# supported by pandoc, but with a different extension
PANDOC_INPUT_FORMAT_MAP = {
    "dbk": "docbook",
    "doku": "dokuwiki",
    "dj": "djot",
    "htm": "html",
    "html5": "html",
    "htmls": "html",
    "xhtml": "html",
    "xhtmls": "html",
    "rest": "rst",
    "tex": "latex",
    "texs": "latex",
    "t2tags": "t2t",
    "txt2t": "t2t",
    "txt2tags": "t2t",
    "typ": "typst",
    "wiki": "vimwiki",  # Are there other wikis using .wiki extension?
}

# fmt: off
INTERMEDIATE_FORMAT = "html"
PANDOC_OUTPUT_FORMAT = (
    # https://pandoc.org/chunkedhtml-demo/8.22-markdown-variants.html
    # Don't use "commonmark_x". There is too much noise.
    "markdown_strict"
    # https://pandoc.org/chunkedhtml-demo/8.5-verbatim-code-blocks.html#extension-backtick_code_blocks
    "+backtick_code_blocks"
    # https://pandoc.org/chunkedhtml-demo/8.21-non-default-extensions.html#extension-mark
    "+mark"
    # https://pandoc.org/chunkedhtml-demo/8.9-tables.html#extension-pipe_tables
    "+pipe_tables"
    # https://pandoc.org/chunkedhtml-demo/8.12-inline-formatting.html#extension-strikeout
    "+strikeout"
    # https://pandoc.org/chunkedhtml-demo/8.12-inline-formatting.html#extension-superscript-subscript
    "+superscript+subscript"
    # https://pandoc.org/chunkedhtml-demo/8.7-lists.html#extension-task_lists
    "+task_lists"
    # https://pandoc.org/chunkedhtml-demo/8.13-math.html#extension-tex_math_dollars
    "+tex_math_dollars"
    # https://pandoc.org/chunkedhtml-demo/8.14-raw-html.html#extension-raw_html
    "-raw_html"
)
# fmt:on


def html_to_markdown(text_html: bytes | str, custom_filter: list | None = None):
    # some needed preprocessing
    soup = BeautifulSoup(text_html, "html.parser")
    if custom_filter is not None:
        for filter_ in custom_filter:
            filter_(soup)
    # pre-filter
    jimmy.md_lib.html_filter.replace_special_characters(soup)
    # main filter
    jimmy.md_lib.html_filter.div_checklists(soup)
    jimmy.md_lib.html_filter.highlighting(soup)
    jimmy.md_lib.html_filter.iframes_to_links(soup)
    jimmy.md_lib.html_filter.merge_single_element_lists(soup)
    jimmy.md_lib.html_filter.remove_bold_header(soup)
    jimmy.md_lib.html_filter.streamline_tables(soup)
    jimmy.md_lib.html_filter.whitespace_in_math(soup)
    # final cleanup
    jimmy.md_lib.html_filter.multiline_markup(soup)
    # jimmy.md_lib.html_filter.remove_empty_elements(soup)
    text_html_filtered = str(soup)

    # writer: json ast -> markdown
    text_md = pypandoc.convert_text(
        text_html_filtered,
        PANDOC_OUTPUT_FORMAT,
        format=INTERMEDIATE_FORMAT,
        extra_args=[
            # don't create artificial line breaks
            "--wrap=preserve",
        ],
    )
    if "[TABLE]" in text_md:
        LOGGER.warning("Table is too complex and can't be converted to markdown.")

    text_md = text_md.replace("{TEMPORARYNEWLINE}", "<br>")
    return text_md.strip()


def markup_to_markdown(
    text: bytes | str,
    format_: str = "html",
    resource_folder: Path = Path("tmp_media"),
    custom_filter: list | None = None,
) -> str:
    # Route everything through this function to get a single path of truth.
    if format_.startswith("html"):
        text_html = text
    else:
        # reader: x -> HTML
        text_html = pypandoc.convert_text(
            text,
            INTERMEDIATE_FORMAT,
            format=format_,
            sandbox=True,
            extra_args=[
                # somehow the temp folder is needed to create the resources properly
                f"--extract-media={resource_folder}",
                # don't create artificial line breaks
                "--wrap=preserve",
            ],
        )

    # HTML filter: HTML -> filter -> HTML
    # writer: HTML -> Markdown
    return html_to_markdown(text_html, custom_filter)


# Problem: "//" is part of many URI (between scheme and host).
# We need to exclude them to prevent unwanted conversions.
NEG_LOOKBEHINDS = "".join(f"(?<!{scheme}:)" for scheme in web_schemes)
double_slash_re = re.compile(rf"{NEG_LOOKBEHINDS}\/\/(.*?){NEG_LOOKBEHINDS}\/\/")
horizontal_line_re = re.compile(r"^-{3,}$", re.MULTILINE)
