"""Helper functions for Markdown links."""

import dataclasses
import re
import xml.etree.ElementTree as ET

import markdown
from markdown.inlinepatterns import InlineProcessor
from markdown.treeprocessors import Treeprocessor
from markdown.extensions import Extension

import jimmy.md_lib.common
import jimmy.md_lib.convert


def make_link(
    text: str, url: str, fragment: str = "", is_image: bool = False, title: str = ""
) -> str:
    """Make a standard Markdown link."""
    title = "" if not title else f' "{title}"'
    fragment = "#" + fragment if fragment else ""
    if url.startswith("<") and url.endswith(">"):
        # include the fragment inside the brackets
        complete_url = f"{url[:-1]}{fragment}{url[-1:]}"
    else:
        complete_url = f"{url}{fragment}"
    return f"{'!' * is_image}[{text}]({complete_url}{title})"


def make_wikilink(text: str, url: str, is_embedded: bool = False, fragment: str = "") -> str:
    """Make a wikilink."""
    text = text if text.strip() == "" else f"|{text}"
    fragment = "#" + fragment if fragment else ""
    return f"{'!' * is_embedded}[[{url}{fragment}{text}]]"


@dataclasses.dataclass
class MarkdownLink:
    """
    Represents a markdown link:
    - link: https://www.markdownguide.org/basic-syntax/#links
    - image: https://www.markdownguide.org/basic-syntax/#images-1

    Links can contain a fragment: https://spec.commonmark.org/0.31.2/#example-501
    In Markdown, it's usually a heading.

    Formats could be:
    - [text](url)
    - ![text](url)
    - [text](<url>)
    - [text](url "title")
    - [text](url#fragment)
    - [[url#fragment]]
    - ![[url]]
    - [[url|text]]
    - [[url#fragment|text]]
    """

    text: str = ""
    url: str = ""
    title: str = ""
    fragment: str = ""
    is_image: bool = False
    is_wikilink: bool = False
    is_embedded: bool = False

    @property
    def is_web_link(self) -> bool:
        return any(
            self.url.startswith(f"{protocol}://") for protocol in jimmy.md_lib.common.web_schemes
        )

    @property
    def is_mail_link(self) -> bool:
        return self.url.startswith("mailto:")

    def __repr__(self) -> str:
        kws = [
            f"{key}={value!r}"
            for key, value in self.__dict__.items()
            if key not in ("fragment", "is_image", "is_wikilink", "is_embedded") or value
        ]
        return f"{type(self).__name__}({', '.join(kws)})"

    def __str__(self) -> str:
        if self.is_wikilink:
            return make_wikilink(self.text, self.url, self.is_embedded, fragment=self.fragment)
        return make_link(
            self.text, self.url, is_image=self.is_image, title=self.title, fragment=self.fragment
        )

    def reformat(self) -> str:
        if not self.url:
            return f"<{self.text}>"
        if self.is_web_link and self.text == self.url:
            return f"<{self.url}>"
        return make_link(
            self.text, self.url, is_image=self.is_image, title=self.title, fragment=self.fragment
        )


class WikiLinkExtension(Extension):
    """Add inline processor to Markdown."""

    def extendMarkdown(self, md):  # noqa: N802
        self.md = md  # pylint: disable=attribute-defined-outside-init

        # append to end of inline patterns
        wikilink_re = r"(!)?\[\[(.+?)(?:\|(.+?))?\]\]"
        wikilink_extension = WikiLinksInlineProcessor(wikilink_re)
        wikilink_extension.md = md
        md.inlinePatterns.register(wikilink_extension, "wikilink", 75)


class WikiLinksInlineProcessor(InlineProcessor):
    """
    Build link from `wikilink`.
    Based on
    https://github.com/Python-Markdown/markdown/blob/89112c293f7b399ae8808f3a06306f46601e9684/markdown/extensions/wikilinks.py
    """

    def handleMatch(  # type: ignore[override]  # noqa: N802
        self, m: re.Match[str], data: str
    ) -> tuple[ET.Element, int, int]:
        # "!" means embedding. It gets converted to a usual link later.
        # https://help.obsidian.md/embeds
        embedded, url, description = m.groups()
        a = ET.Element("a")
        if description is not None and description.strip():
            a.text = description
        a.set("href", url)
        a.set("wikilink", "")
        if embedded:
            a.set("embedded", "")
        return a, m.start(0), m.end(0)


def split_url_fragment(url: str) -> tuple[str, ...]:
    """
    Split a fragment from an URL. Usually the URL is a path to a note and the fragment
    is a heading ID, like `./path/to/my_note.md#heading`.
    """
    url_splitted = url.split("#", 1)
    match len(url_splitted):
        case 0:
            url = ""
            fragment = ""
        case 1:
            url = url_splitted[0]
            fragment = ""
        case 2:
            url, fragment = url_splitted
    return url, fragment


class LinkExtractor(Treeprocessor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pandoc = jimmy.md_lib.convert.MarkupConverter()

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
            text += self.pandoc.markup_to_markdown(
                "".join(
                    ET.tostring(child, encoding="unicode", method="html") for child in list(link)
                ),
                standalone=False,
            )
            url, fragment = split_url_fragment(self.unescape(url))
            self.md.links.append(
                MarkdownLink(
                    self.unescape(text),
                    url,
                    self.unescape(title),
                    fragment=fragment,
                    is_wikilink=link.get("wikilink") is not None,
                    is_embedded=link.get("embedded") is not None,
                )
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


MD = markdown.Markdown(extensions=[WikiLinkExtension(), LinkExtractorExtension()])


def get_markdown_links(text: str) -> list[MarkdownLink]:
    # ruff: noqa: E501
    # pylint: disable=line-too-long
    # doctest has too long lines
    r"""
    Get standard Markdown links and wikilinks.

    >>> import logging
    >>> logging.getLogger().setLevel("INFO")
    >>> jimmy.main.add_binaries_to_path()  # hack to provide pandoc
    >>> get_markdown_links('```\n[link](:/custom)\n```')
    []
    >>> get_markdown_links('`[link](:/custom)`')
    []
    >>> get_markdown_links('[link](url://with spaces)')
    [MarkdownLink(text='link', url='url://with spaces', title='')]
    >>> get_markdown_links('[link](url#fragment)')
    [MarkdownLink(text='link', url='url', title='', fragment='fragment')]

    # bracketed URLs are handled later in a fallback
    >>> get_markdown_links('[link](<./with spaces.md>)')
    [MarkdownLink(text='link', url='./with spaces.md', title='')]
    >>> get_markdown_links("![](image.png)")
    [MarkdownLink(text='', url='image.png', title='', is_image=True)]
    >>> get_markdown_links("![abc](image (1).png)")
    [MarkdownLink(text='abc', url='image (1).png', title='', is_image=True)]
    >>> get_markdown_links("[mul](tiple) [links](...)") # doctest: +NORMALIZE_WHITESPACE
    [MarkdownLink(text='mul', url='tiple', title=''),
     MarkdownLink(text='links', url='...', title='')]
    >>> get_markdown_links("![desc \\[reference\\]](Image.png){#fig:leanCycle}")
    [MarkdownLink(text='desc \\[reference\\]', url='Image.png', title='', is_image=True)]
    >>> get_markdown_links('[link](internal "Example Title")')
    [MarkdownLink(text='link', url='internal', title='Example Title')]
    >>> get_markdown_links('[link](#internal)')
    [MarkdownLink(text='link', url='', title='', fragment='internal')]
    >>> get_markdown_links('[link](:/custom)')
    [MarkdownLink(text='link', url=':/custom', title='')]
    >>> get_markdown_links('[weblink](https://duckduckgo.com)')
    [MarkdownLink(text='weblink', url='https://duckduckgo.com', title='')]
    >>> get_markdown_links('[red\\_500x500.png]()')
    [MarkdownLink(text='red\\_500x500.png', url='', title='')]
    >>> get_markdown_links('[\\<weblink\\>]()')
    [MarkdownLink(text='\\<weblink\\>', url='', title='')]
    >>> get_markdown_links('[foo `bar` baz](:/custom)')
    [MarkdownLink(text='foo `bar` baz', url=':/custom', title='')]
    >>> get_markdown_links('[foo **`nested` bar** *baz* pow](:/custom)')
    [MarkdownLink(text='foo **`nested` bar** *baz* pow', url=':/custom', title='')]

    # wikilinks
    >>> get_markdown_links('```\n[[link]]\n```')
    []
    >>> get_markdown_links('`[[link]]`')
    []
    >>> get_markdown_links('![[link]]')
    [MarkdownLink(text='', url='link', title='', is_wikilink=True, is_embedded=True)]
    >>> get_markdown_links('[[image.png]]')
    [MarkdownLink(text='', url='image.png', title='', is_wikilink=True)]
    >>> get_markdown_links('[[url#fragment|tit le]]')
    [MarkdownLink(text='tit le', url='url', title='', fragment='fragment', is_wikilink=True)]
    >>> get_markdown_links("[[multiple]] [[links]]") # doctest: +NORMALIZE_WHITESPACE
    [MarkdownLink(text='', url='multiple', title='', is_wikilink=True),
     MarkdownLink(text='', url='links', title='', is_wikilink=True)]
    >>> get_markdown_links('[[internal|Example Title]]')
    [MarkdownLink(text='Example Title', url='internal', title='', is_wikilink=True)]
    >>> get_markdown_links('[[#internal]]')
    [MarkdownLink(text='', url='', title='', fragment='internal', is_wikilink=True)]

    # TODO:
    # >>> get_markdown_links('[<DIV>.tiddler file format](tiddlywiki://TiddlerFiles)')
    # [MarkdownLink(text='<DIV>.tiddler file format', url='tiddlywiki://TiddlerFiles',
    #  title='')]
    # >>> get_markdown_links('<<list "[Plug](Plug) -[dr.of](dr.of)">>')  # doctest: +NORMALIZE_WHITESPACE
    # [MarkdownLink(text='Plug', url='Plug', title=''),
    #  MarkdownLink(text='dr.of', url='dr.of', title='')]
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
