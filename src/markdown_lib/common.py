"""Common Markdown functions."""

from dataclasses import dataclass, field
import logging
from pathlib import Path
import re

from bs4 import BeautifulSoup
import markdown
from markdown.treeprocessors import Treeprocessor
from markdown.extensions import Extension
import pypandoc

import markdown_lib.html_preprocessing


LOGGER = logging.getLogger("jimmy")


def split_h1_title_from_body(markdown_: str) -> tuple[str, str]:
    # TODO: doctest
    try:
        title, body = markdown_.split("\n", maxsplit=1)
    except ValueError:
        title = markdown_
        body = ""
    return title.lstrip("# "), body.lstrip()


@dataclass
class MarkdownTable:
    """Construct a Markdown table from lists."""

    header_rows: list[list[str]] = field(default_factory=list)
    data_rows: list[list[str]] = field(default_factory=list)
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


@dataclass
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
        # not robust, but sufficient for now
        return self.url.startswith("http")

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
                    self.unescape(image.get("alt")), image.get("src"), is_image=True
                )
            )
        for link in root.findall(".//a"):
            url = link.get("href")
            if (title := link.get("title")) is not None:
                # TODO: This is not robust against titles with quotation marks.
                if url:
                    url += f' "{title}"'
                else:
                    url = title  # don't add a title if there is no url
            self.md.links.append(MarkdownLink(link.text, url))


class LinkExtractorExtension(Extension):
    def extendMarkdown(self, md):  # noqa: N802
        link_extension = LinkExtractor(md)
        md.treeprocessors.register(link_extension, "link_extension", 15)


MD = markdown.Markdown(extensions=[LinkExtractorExtension()])


def get_markdown_links(text: str) -> list[MarkdownLink]:
    """
    >>> get_markdown_links("![](image.png)")
    [MarkdownLink(text='', url='image.png', is_image=True)]
    >>> get_markdown_links("![abc](image (1).png)")
    [MarkdownLink(text='abc', url='image (1).png', is_image=True)]
    >>> get_markdown_links("[mul](tiple) [links](...)") # doctest: +NORMALIZE_WHITESPACE
    [MarkdownLink(text='mul', url='tiple', is_image=False),
     MarkdownLink(text='links', url='...', is_image=False)]
    >>> get_markdown_links("![desc \\[reference\\]](Image.png){#fig:leanCycle}")
    [MarkdownLink(text='desc \\\\[reference\\\\]', url='Image.png', is_image=True)]
    >>> get_markdown_links('[link](internal "Example Title")')
    [MarkdownLink(text='link', url='internal "Example Title"', is_image=False)]
    >>> get_markdown_links('[link](#internal)')
    [MarkdownLink(text='link', url='#internal', is_image=False)]
    >>> get_markdown_links('[link](:/custom)')
    [MarkdownLink(text='link', url=':/custom', is_image=False)]
    >>> get_markdown_links('[weblink](https://duckduckgo.com)')
    [MarkdownLink(text='weblink', url='https://duckduckgo.com', is_image=False)]
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


# markdown output formats:
# https://pandoc.org/chunkedhtml-demo/8.22-markdown-variants.html
# Don't use "commonmark_x". There would be too many noise.
# fmt: off
PANDOC_OUTPUT_FORMAT = (
    "markdown_strict"
    "+pipe_tables"
    "+backtick_code_blocks"
    "+task_lists"
    "-raw_html"
)
# fmt:on


def markup_to_markdown(text: str, format_: str = "html") -> str:
    if format_ == "html":
        # some needed preprocessing
        soup = BeautifulSoup(text, "html.parser")
        markdown_lib.html_preprocessing.div_checklists(soup)
        markdown_lib.html_preprocessing.iframes_to_links(soup)
        markdown_lib.html_preprocessing.streamline_tables(soup)
        markdown_lib.html_preprocessing.synology_note_station_fix_img_src(soup)
        text = str(soup)
    text_md = pypandoc.convert_text(
        text,
        PANDOC_OUTPUT_FORMAT,
        format=format_,
        sandbox=True,
        extra_args=["--wrap=none"],
    )
    if "[TABLE]" in text_md:
        LOGGER.warning("Table is too complex and can't be converted to markdown.")

    text_md = text_md.replace("{TEMPORARYNEWLINE}", "<br>")
    return text_md.strip()


def file_to_markdown(file_: Path, resource_folder: Path) -> str:
    # TODO: apply HTML preprocessing here, too
    # if file_.suffix == ".html":
    #     return markup_to_markdown(
    #         file_.read_text(encoding="utf-8"), format_=file_.suffix.lstrip(".")
    #     )
    file_md = pypandoc.convert_file(
        file_,
        PANDOC_OUTPUT_FORMAT,
        sandbox=True,  # offline mode
        extra_args=[
            # somehow the temp folder is needed to create the resources properly
            f"--extract-media={resource_folder}",
            # don't create artificial line breaks
            "--wrap=none",
        ],
    )
    if "[TABLE]" in file_md:
        LOGGER.warning("Table is too complex and can't be converted to markdown.")
    return file_md.strip()


# Problem: "//" is part of many URI (between scheme and host).
# We need to exclude them to prevent unwanted conversions.
# https://en.wikipedia.org/wiki/List_of_URI_schemes
schemes = [
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
NEG_LOOKBEHINDS = "".join(f"(?<!{scheme}:)" for scheme in schemes)
double_slash_re = re.compile(rf"{NEG_LOOKBEHINDS}\/\/(.*?){NEG_LOOKBEHINDS}\/\/")
horizontal_line_re = re.compile(r"^-{3,}$", re.MULTILINE)
