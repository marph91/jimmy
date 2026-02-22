"""Helper functions to convert between formats."""

import logging
from pathlib import Path

from bs4 import BeautifulSoup
import pypandoc

import jimmy.md_lib.html_filter

LOGGER = logging.getLogger("jimmy")


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
    # https://pandoc.org/MANUAL.html#markdown-variants
    # Don't use "commonmark_x". There is too much noise.
    "markdown_strict"
    # https://pandoc.org/MANUAL.html#extension-all_symbols_escapable
    "+all_symbols_escapable"
    # https://pandoc.org/MANUAL.html#extension-backtick_code_blocks
    "+backtick_code_blocks"
    # https://pandoc.org/MANUAL.html#extension-mark
    "+mark"
    # https://pandoc.org/MANUAL.html#extension-pipe_tables
    "+pipe_tables"
    # https://pandoc.org/MANUAL.html#extension-space_in_atx_header
    "+space_in_atx_header"
    # https://pandoc.org/MANUAL.html#extension-strikeout
    "+strikeout"
    # https://pandoc.org/MANUAL.html#extension-superscript-subscript
    "+superscript+subscript"
    # https://pandoc.org/MANUAL.html#extension-task_lists
    "+task_lists"
    # https://pandoc.org/MANUAL.html#extension-tex_math_dollars
    "+tex_math_dollars"
    # https://pandoc.org/MANUAL.html#extension-raw_html
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
    jimmy.md_lib.html_filter.link_internal_headings(soup)
    jimmy.md_lib.html_filter.merge_consecutive_formatting(soup)
    jimmy.md_lib.html_filter.merge_single_element_lists(soup)
    jimmy.md_lib.html_filter.remove_bold_header(soup)
    jimmy.md_lib.html_filter.remove_duplicated_links(soup)
    jimmy.md_lib.html_filter.streamline_tables(soup)
    jimmy.md_lib.html_filter.underline(soup)
    jimmy.md_lib.html_filter.strikethrough(soup)
    jimmy.md_lib.html_filter.whitespace_in_math(soup)
    # final cleanup
    jimmy.md_lib.html_filter.multiline_markup(soup)
    jimmy.md_lib.html_filter.unwrap_inline_whitespace(soup)
    jimmy.md_lib.html_filter.remove_empty_markup(soup)
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

    text_md = text_md.replace("{TEMPORARYCHECKBOXCHECKED}", "[x]")
    text_md = text_md.replace("{TEMPORARYCHECKBOXUNCHECKED}", "[ ]")
    text_md = text_md.replace("{TEMPORARYNEWLINE}", "<br>")
    return text_md.strip()


def markup_to_markdown(
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    text: bytes | str,
    pwd: Path | None = None,  # input
    format_: str = "html",
    resource_folder: Path = Path("tmp_media"),  # output
    standalone: bool = True,
    custom_filter: list | None = None,
    extra_args: list | None = None,
) -> str:
    # Route everything through this function to get a single path of truth.
    if format_.startswith("html"):
        text_html = text
    else:
        if extra_args is None:
            extra_args = []
        extra_args.extend(
            [
                # somehow the temp folder is needed to create the resources properly
                f"--extract-media={resource_folder}",
                # don't create artificial line breaks
                "--wrap=preserve",
                # mathml seems cover the widest range of formulas
                # https://pandoc.org/MANUAL.html#math-rendering-in-html
                "--mathml",
            ]
        )
        if standalone:
            extra_args.append("--standalone")
        # reader: x -> HTML
        text_html = pypandoc.convert_text(
            text,
            INTERMEDIATE_FORMAT,
            format=format_,
            # Don't use sandbox to preserve linked files, like in asciidoc.
            # sandbox=True,
            extra_args=extra_args,
            # Resource path didn't work. Use pwd instead.
            # https://pandoc.org/MANUAL.html#reader-options
            # separator = ";" if platform.system().lower() == "windows" else ":"
            # extra_args.append(f"--resource-path={resource_path}")
            cworkdir=pwd,
        )

    # HTML filter: HTML -> filter -> HTML
    # writer: HTML -> Markdown
    return html_to_markdown(text_html, custom_filter)
