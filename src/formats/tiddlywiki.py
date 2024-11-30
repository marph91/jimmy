"""Convert TiddlyWiki notes to the intermediate format."""

import base64
import datetime as dt
from html.parser import HTMLParser
import logging
import json
from pathlib import Path

import common
import converter
import intermediate_format as imf
import markdown_lib.common
import markdown_lib.tiddlywiki

LOGGER = logging.getLogger("jimmy")


class MarkdownHtmlSeparator(HTMLParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.active_html_tags = []
        self.md = []
        self.html = []

    def handle_starttag(self, tag, attrs):
        # ignore void elements: https://developer.mozilla.org/en-US/docs/Glossary/Void_element
        if tag not in (
            "area",
            "base",
            "br",
            "col",
            "embed",
            "hr",
            "img",
            "input",
            "link",
            "meta",
            "param",
            "source",
            "track",
            "wbr",
        ):
            self.active_html_tags.append(tag)
        attributes_html = []
        for key, value in attrs:
            attributes_html.append(f' {key}="{value}"')
        attributes_html_string = "".join(attributes_html)
        self.html.append(f"<{tag}{attributes_html_string}>")

    def handle_endtag(self, tag):
        if not self.active_html_tags:
            LOGGER.debug(f'Unexpected closing tag "{tag}"')
        elif (opening_tag := self.active_html_tags.pop(-1)) != tag:
            LOGGER.warning(
                f'Closing tag "{tag}" doesn\'t match opening tag "{opening_tag}"'
            )
            raise ValueError()
        else:
            self.html.append(f"</{tag}>")

    def handle_data(self, data):
        if not self.active_html_tags:
            if not data.strip() and self.html:
                # if data is only whitespace and there is HTML, just append it.
                self.html.append(data)
            else:
                self.handle_remaining_html()
                self.md.append(data)
        else:
            self.html.append(data)

    def handle_remaining_html(self):
        if self.html:
            # TODO: minimize calls, as pandoc is slow
            self.md.append(markdown_lib.common.markup_to_markdown("".join(self.html)))
            self.html = []

    def get_md(self) -> str:
        if self.active_html_tags:
            LOGGER.warning(f'Unexpected open tags: {" ".join(self.active_html_tags)}')
            raise ValueError()
        self.handle_remaining_html()
        return "".join(self.md)


def wikitext_html_to_md(wikitext_html: str) -> str:
    # convert wikitext + HTML to markdown + HTML
    md_html = markdown_lib.tiddlywiki.wikitext_to_md(wikitext_html)

    # convert remaining HTML to markdown
    # Wikitext can contain HTML: https://tiddlywiki.com/#HTML%20in%20WikiText
    parser = MarkdownHtmlSeparator()
    try:
        parser.feed(md_html)
        return parser.get_md()
    except ValueError:
        return md_html


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
    accepted_extensions = [".json", ".tid"]
    accept_folder = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # we need a resource folder to avoid writing files to the source folder
        self.resource_folder = common.get_temp_folder()

    def convert_json(self, file_or_folder: Path):
        file_dict = json.loads(file_or_folder.read_text(encoding="utf-8"))
        for tiddler in file_dict:
            title = tiddler["title"]
            self.logger.debug(f'Converting note "{title}"')

            resources = []
            mime = tiddler.get("type", "")
            if mime == "image/svg+xml":
                continue  # TODO
            if (
                mime.startswith("image/")
                or mime == "application/pdf"
                or mime == "audio/mp3"
            ):
                if (text_base64 := tiddler.get("text")) is not None:
                    # Use the original filename if possible.
                    # TODO: Files with same name are replaced.
                    resource_title = tiddler.get("alt-text")
                    temp_filename = self.resource_folder / (
                        common.unique_title()
                        if resource_title is None
                        else resource_title
                    )
                    temp_filename.write_bytes(base64.b64decode(text_base64))
                    body = f"![{temp_filename.name}]({temp_filename})"
                    resources.append(imf.Resource(temp_filename, body, resource_title))
                elif (source := tiddler.get("source")) is not None:
                    body = f"![{title}]({source})"
                elif (uri := tiddler.get("_canonical_uri")) is not None:
                    body = f"[{title}]({uri})"
                else:
                    body = wikitext_html_to_md(tiddler.get("text", ""))
                    self.logger.warning(f"Unhandled attachment type {mime}")
            elif mime == "application/json":
                body = "```\n" + tiddler.get("text", "") + "\n```"
            else:
                body = wikitext_html_to_md(tiddler.get("text", ""))

            note_imf = imf.Note(
                title,
                body,
                author=tiddler.get("creator"),
                source_application=self.format,
                # Tags don't have a separate id. Just use the name as id.
                tags=[imf.Tag(tag) for tag in split_tags(tiddler.get("tags", ""))],
                resources=resources,
            )
            if "created" in tiddler:
                note_imf.created = tiddlywiki_to_datetime(tiddler["created"])
            if "modified" in tiddler:
                note_imf.updated = tiddlywiki_to_datetime(tiddler["modified"])
            if any(t.reference_id.startswith("$:/tags/") for t in note_imf.tags):
                continue  # skip notes with special tags
            self.root_notebook.child_notes.append(note_imf)

    def convert_tid(self, file_or_folder: Path):
        tiddler = file_or_folder.read_text(encoding="utf-8")
        metadata_raw, body_wikitext = tiddler.split("\n\n", maxsplit=1)

        metadata = {}
        for line in metadata_raw.split("\n"):
            key, value = line.split(": ", 1)
            metadata[key] = value

        title = metadata["title"]
        self.logger.debug(f'Converting note "{title}"')

        note_imf = imf.Note(
            title,
            wikitext_html_to_md(body_wikitext),
            author=metadata.get("creator"),
            source_application=self.format,
            tags=[imf.Tag(tag) for tag in split_tags(metadata.get("tags", ""))],
            created=tiddlywiki_to_datetime(metadata["created"]),
            updated=tiddlywiki_to_datetime(metadata["modified"]),
        )
        self.root_notebook.child_notes.append(note_imf)

    def convert(self, file_or_folder: Path):
        if file_or_folder.suffix == ".json":
            self.convert_json(file_or_folder)
        elif file_or_folder.suffix == ".tid":
            self.convert_tid(file_or_folder)
        else:  # folder of .tid
            for tid_file in sorted(file_or_folder.glob("*.tid")):
                self.convert_tid(tid_file)
