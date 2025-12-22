"""Helper functions for Markdown links."""

import dataclasses
import re
import xml.etree.ElementTree as ET

import markdown
from markdown.treeprocessors import Treeprocessor
from markdown.extensions import Extension

import jimmy.md_lib.common
import jimmy.md_lib.convert


def make_link(text: str, url: str, is_image: bool = False, title: str = "") -> str:
    return f"{'!' * is_image}[{text}]({url}{title})"


@dataclasses.dataclass
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
        return any(
            self.url.startswith(f"{protocol}://") for protocol in jimmy.md_lib.common.web_schemes
        )

    @property
    def is_mail_link(self) -> bool:
        return self.url.startswith("mailto:")

    def __str__(self) -> str:
        title = "" if not self.title else f' "{self.title}"'
        return make_link(self.text, self.url, is_image=self.is_image, title=title)

    def reformat(self) -> str:
        if not self.url:
            return f"<{self.text}>"
        if self.is_web_link and self.text == self.url:
            return f"<{self.url}>"
        title = "" if not self.title else f' "{self.title}"'
        return make_link(self.text, self.url, is_image=self.is_image, title=title)


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
                    self.unescape(image.get("src", "")),
                    self.unescape(image.get("title", "")),
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
            # Convert any remaining HTML nodes back to Markdown.
            # This might alter the original link text.
            text += jimmy.md_lib.convert.markup_to_markdown(
                "".join(
                    ET.tostring(child, encoding="unicode", method="html") for child in list(link)
                ),
                standalone=False,
            )
            self.md.links.append(
                MarkdownLink(self.unescape(text), self.unescape(url), self.unescape(title))
            )


class LinkExtractorExtension(Extension):
    def extendMarkdown(self, md):  # noqa: N802
        link_extension = LinkExtractor(md)
        # priority:
        # https://python-markdown.github.io/reference/markdown/treeprocessors/#markdown.treeprocessors.build_treeprocessors
        md.treeprocessors.register(link_extension, "link_extension", 15)
        # deregister default, but unneeded treeprocessors
        md.treeprocessors.deregister("prettify")
        md.treeprocessors.deregister("unescape")


MD = markdown.Markdown(extensions=[LinkExtractorExtension()])


def get_markdown_links(text: str) -> list[MarkdownLink]:
    # ruff: noqa: E501
    # pylint: disable=line-too-long
    # doctest has too long lines
    r"""
    >>> import logging
    >>> logging.getLogger().setLevel("INFO")
    >>> jimmy.main.add_binaries_to_path()  # hack to provide pandoc
    >>> get_markdown_links('```\n[link](:/custom)\n```')
    []
    >>> get_markdown_links('`[link](:/custom)`')
    []
    >>> get_markdown_links('[link](url://with spaces)')
    [MarkdownLink(text='link', url='url://with spaces', title='', is_image=False)]
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
    >>> get_markdown_links('[red\\_500x500.png]()')
    [MarkdownLink(text='red\\_500x500.png', url='', title='', is_image=False)]
    >>> get_markdown_links('[\\<weblink\\>]()')
    [MarkdownLink(text='\\<weblink\\>', url='', title='', is_image=False)]
    >>> get_markdown_links('[foo `bar` baz](:/custom)')
    [MarkdownLink(text='foo `bar` baz', url=':/custom', title='', is_image=False)]
    >>> get_markdown_links('[foo **`nested` bar** *baz* pow](:/custom)')
    [MarkdownLink(text='foo **`nested` bar** *baz* pow', url=':/custom', title='', is_image=False)]

    # TODO:
    # >>> get_markdown_links('[<DIV>.tiddler file format](tiddlywiki://TiddlerFiles)')
    # [MarkdownLink(text='<DIV>.tiddler file format', url='tiddlywiki://TiddlerFiles',
    #  title='', is_image=False)]
    # >>> get_markdown_links('<<list "[Plug](Plug) -[dr.of](dr.of)">>')  # doctest: +NORMALIZE_WHITESPACE
    # [MarkdownLink(text='Plug', url='Plug', title='', is_image=False),
    #  MarkdownLink(text='dr.of', url='dr.of', title='', is_image=False)]
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
