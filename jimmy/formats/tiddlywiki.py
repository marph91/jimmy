"""Convert TiddlyWiki notes to the intermediate format."""

import datetime as dt
from html.parser import HTMLParser
import logging
import json
from pathlib import Path
import string

from jimmy import common, converter, intermediate_format as imf
import jimmy.md_lib.common
import jimmy.md_lib.tiddlywiki

LOGGER = logging.getLogger("jimmy")


# https://developer.mozilla.org/en-US/docs/Glossary/Void_element
HTML_VOID_ELEMENTS = (
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
)

# https://tiddlywiki.com/static/Variables.html
# https://tiddlywiki.com/static/Core%2520Variables.html
TIDDLYWIKI_CORE_VARIABLES = (
    "actionTiddler",
    "actionTiddlerList",
    "currentTab",
    "currentTiddler",
    "modifier",
    "namespace",
    "storyTiddler",
    "thisTiddler",
    "transclusion",
    "tv-history-list",
    "tv-show-missing-links",
    "tv-story-list",
    "tv-tiddler-preview",
    "tv-adjust-heading-level",
    "tv-auto-open-on-import",
    "tv-config-static",
    "tv-config-toolbar-class",
    "tv-config-toolbar-icons",
    "tv-config-toolbar-text",
    "tv-filter-export-link",
    "tv-get-export-image-link",
    "tv-get-export-link",
    "tv-get-export-path",
    "tv-wikilink-template",
    "tv-wikilink-tooltip",
    "tv-wikilinks",
)
# https://tiddlywiki.com/static/Core%2520Widgets.html
TIDDLYWIKI_CORE_WIDGETS = (
    "action-confirm",
    "action-createtiddler",
    "action-deletefield",
    "action-deletetiddler",
    "action-listops",
    "action-log",
    "action-navigate",
    "action-popup",
    "action-sendmessage",
    "action-setfield",
    "action-setmultiplefields",
    "ActionWidget Execution Modes",
    "ActionWidgets",
    "browse",
    # "button",  # TODO: button is a valid HTML tag, too
    "checkbox",
    "codeblock",
    "count",
    "data",
    "diff-text",
    "draggable",
    "droppable",
    "dropzone",
    "edit-bitmap",
    "edit-text",
    "edit",
    "encrypt",
    "entity",
    "error",
    "EventCatcherWidget",
    "fieldmangler",
    "fields",
    "fill",
    "genesis",
    "image",
    "importvariables",
    "jsontiddler",
    "keyboard",
    "let",
    "linkcatcher",
    "link",
    "list",
    "LogWidget",
    "macrocall",
    "MessageCatcherWidget",
    "MessageHandlerWidgets",
    "navigator",
    "parameters",
    "password",
    "vars",
    "radio",
    "range",
    "reveal",
    "scrollable",
    "select",
    "setmultiplevariables",
    "setvariable",
    "set",
    "slot",
    "testcase",
    "text",
    "tiddler",
    "transclude",
    "TriggeringWidgets",
    "vars",
    "view",
    "wikify",
)
# https://tiddlywiki.com/static/Core%2520Macros.html
TIDDLYWIKI_CORE_MACROS = (
    "changecount",
    "colour",
    "colour-picker",
    "contrastcolour",
    "copy-to-clipboard",
    "csvtiddlers",
    "datauri",
    "dumpvariables",
    "image-picker",
    "jsontiddler",
    "jsontiddlers",
    "keyboard-driven-input",
    "lingo",
    "list-links",
    "list-links-draggable",
    "list-tagged-draggable",
    "list-thumbnails",
    "Macros",
    "makedatauri",
    "now",
    "qualify",
    "resolvepath",
    "show-filter-count",
    "Stylesheet Macros",
    "Table-of-Contents Macros",
    "tabs",
    "tag",
    "tag-picker",
    "tag-pill",
    "thumbnail",
    "timeline",
    "translink",
    "tree",
    "unusedtitle",
    "version",
)
TIDDLYWIKI_CORE_ELEMENTS = tuple(
    element.lower()
    for element in TIDDLYWIKI_CORE_VARIABLES + TIDDLYWIKI_CORE_WIDGETS + TIDDLYWIKI_CORE_MACROS
)


class MarkdownHtmlSeparator(HTMLParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.active_html_tags = []
        self.md = []
        self.html = []

    def handle_starttag(self, tag, attrs):
        # collect attributes
        attributes_html = []
        for key, value in attrs:
            # TODO: case is lost
            if value is None:
                attributes_html.append(f" {key}")
            else:
                attributes_html.append(f' {key}="{value}"')
        attributes_html_string = "".join(attributes_html)

        if tag in TIDDLYWIKI_CORE_ELEMENTS:  # both are lower case
            # keep as-is
            self.md.append(f"<{tag}{attributes_html_string}>")
            return

        # ignore void elements
        if tag not in HTML_VOID_ELEMENTS:
            self.active_html_tags.append(tag)
        self.html.append(f"<{tag}{attributes_html_string}>")

    def handle_endtag(self, tag):
        if tag in HTML_VOID_ELEMENTS:
            self.html.append(f"</{tag}>")
        elif not self.active_html_tags:
            LOGGER.debug(f'Unexpected closing tag "{tag}"')
        elif (opening_tag := self.active_html_tags.pop(-1)) != tag:
            LOGGER.warning(
                f'Closing tag "{tag}" doesn\'t match opening tag "{opening_tag}" '
                "Returning plain wikitext."
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
            self.md.append(jimmy.md_lib.common.markup_to_markdown("".join(self.html)))
            self.html = []

    def get_md(self) -> str:
        if self.active_html_tags:
            LOGGER.warning(
                f"Unexpected open tags: {' '.join(self.active_html_tags)}. "
                "Returning plain wikitext."
            )
            raise ValueError()
        self.handle_remaining_html()
        return "".join(self.md)


def wikitext_html_to_md(wikitext_html: str) -> str:
    # convert wikitext + HTML to markdown + HTML
    # TODO: slow
    md_html = jimmy.md_lib.tiddlywiki.wikitext_to_md(wikitext_html)

    # convert remaining HTML to markdown
    # Wikitext can contain HTML: https://tiddlywiki.com/#HTML%20in%20WikiText
    parser = MarkdownHtmlSeparator()
    try:
        parser.feed(md_html)
        return parser.get_md()
    except ValueError as exc:
        if str(exc):
            LOGGER.error(f"HTML conversion error: {exc}")
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


def count_upper_case_letters(word: str) -> int:
    """
    >>> count_upper_case_letters("PascalCase")
    2
    >>> count_upper_case_letters("Pascalcase")
    1
    >>> count_upper_case_letters("")
    0
    """
    return sum(1 for character in word if character.isupper())


def is_escaped_link(word: str) -> bool:
    """
    >>> is_escaped_link("JavaScript")
    False
    >>> is_escaped_link("JavaScript~")
    False
    >>> is_escaped_link("~JavaScript")
    True
    >>> is_escaped_link("(~JavaScript")
    True
    >>> is_escaped_link("~(JavaScript")
    True
    """
    for character in word:
        if character == "~":
            return True
        if character in string.ascii_letters:
            return False
    return False


class Converter(converter.BaseConverter):
    ############################################################
    # common functions
    ############################################################

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # we need a resource folder to avoid writing files to the source folder
        self.resource_folder = common.get_temp_folder()

        self.pascalcase_title_note_id_map = {}

    @staticmethod
    def add_tags_to_body(note: imf.Note):
        """In Tiddlywiki, tags are links. This function replicates this behavior."""
        if note.tags:
            tags_md = []
            for tag in note.tags:
                tag_link = f"[{tag.title}]({tag.title})"
                tags_md.append(tag_link)
                note.note_links.append(imf.NoteLink(tag_link, tag.title, tag.title))
            note.body = ", ".join(tags_md) + "\n\n" + note.body

    def handle_markdown_links(self, body: str) -> imf.NoteLinks:
        note_links = []
        for link in jimmy.md_lib.common.get_markdown_links(body):
            if link.url.startswith("tiddlywiki://"):
                # internal link
                linked_note_id = link.url[len("tiddlywiki://") :]
                note_links.append(imf.NoteLink(str(link), linked_note_id, link.text))
        return note_links

    def handle_pascal_case_links(self):
        """
        Replace all words that are in PascalCase and matching to a note title by links.

        TiddlyWiki implementation:
        https://github.com/TiddlyWiki/TiddlyWiki5/blob/61619c07c810108601cd08634928b3f91d0ed269/plugins/tiddlywiki/tw2parser/wikitextrules.js#L25-L30
        Simplified: "(?:(?:[A-Z]+[a-z]+[A-Z][A-Za-z]*)|(?:[A-Z]{2,}[a-z]+))"
        I.e. single words like Camel are not linked.
        """
        for note in self.root_notebook.get_all_child_notes():
            pascal_case_links = set()
            new_note_body_lines = []
            for line in note.body.split("\n"):
                new_line = []
                for word in line.split(" "):
                    if is_escaped_link(word):
                        new_line.append(word)
                        continue  # escaped link
                    word_no_punctuation = word.strip(string.punctuation)
                    if (
                        common.is_pascal_case(word_no_punctuation)
                        and count_upper_case_letters(word_no_punctuation) > 1
                        and word_no_punctuation in self.pascalcase_title_note_id_map
                    ):
                        pascal_case_links.add(word_no_punctuation)
                        new_line.append(
                            word.replace(
                                word_no_punctuation,
                                f"[{word_no_punctuation}](tiddlywiki://{word_no_punctuation})",
                            )
                        )
                    else:
                        new_line.append(word)
                new_note_body_lines.append(" ".join(new_line))
            for link in pascal_case_links:
                note.note_links.append(
                    imf.NoteLink(
                        f"[{link}](tiddlywiki://{link})",
                        self.pascalcase_title_note_id_map[link],
                        link,
                    )
                )
            note.body = "\n".join(new_note_body_lines)

    ############################################################
    # .json conversion
    ############################################################

    @common.catch_all_exceptions
    def convert_note_json(self, tiddler):
        title = tiddler["title"]
        self.logger.debug(f'Converting note "{title}"')

        self.pascalcase_title_note_id_map[common.to_pascal_case(title)] = title

        resources = []
        mime = tiddler.get("type", "")
        if mime == "image/svg+xml":
            return  # TODO
        if mime.startswith("image/") or mime == "application/pdf" or mime == "audio/mp3":
            if (text_base64 := tiddler.get("text")) is not None:
                # Use the original filename if possible.
                resource_title = tiddler.get("alt-text")
                temp_filename = self.resource_folder / (
                    common.unique_title() if resource_title is None else resource_title
                )
                temp_filename = common.write_base64(temp_filename, text_base64)
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
            note_links=self.handle_markdown_links(body),
            original_id=title,
        )
        if "created" in tiddler:
            note_imf.created = tiddlywiki_to_datetime(tiddler["created"])
        if "modified" in tiddler:
            note_imf.updated = tiddlywiki_to_datetime(tiddler["modified"])
        if any(t.reference_id.startswith("$:/tags/") for t in note_imf.tags):
            return  # skip notes with special tags
        self.add_tags_to_body(note_imf)
        self.root_notebook.child_notes.append(note_imf)

    def convert_json(self, file_or_folder: Path):
        input_json = json.loads(file_or_folder.read_text(encoding="utf-8"))
        for tiddler in input_json:
            self.convert_note_json(tiddler)

    ############################################################
    # .tid conversion
    ############################################################

    @common.catch_all_exceptions
    def convert_note(self, file_or_folder: Path):
        tiddler = file_or_folder.read_text(encoding="utf-8")
        try:
            metadata_raw, body_wikitext = tiddler.split("\n\n", maxsplit=1)
        except ValueError:
            metadata_raw = ""
            body_wikitext = tiddler

        metadata = {}
        for line in metadata_raw.split("\n"):
            key, value = line.split(": ", 1)
            metadata[key] = value

        title = metadata["title"]
        self.logger.debug(f'Converting note "{title}"')

        self.pascalcase_title_note_id_map[common.to_pascal_case(title)] = title

        body = wikitext_html_to_md(body_wikitext)
        note_imf = imf.Note(
            title,
            body,
            author=metadata.get("creator"),
            source_application=self.format,
            tags=[imf.Tag(tag) for tag in split_tags(metadata.get("tags", ""))],
            created=tiddlywiki_to_datetime(metadata["created"]),
            updated=tiddlywiki_to_datetime(metadata["modified"]),
            note_links=self.handle_markdown_links(body),
            original_id=title,
        )
        self.add_tags_to_body(note_imf)
        self.root_notebook.child_notes.append(note_imf)

    def convert(self, file_or_folder: Path):
        if file_or_folder.suffix == ".json":
            self.convert_json(file_or_folder)
        elif file_or_folder.suffix == ".tid":
            self.convert_note(file_or_folder)
        else:  # folder of .tid
            for tid_file in sorted(file_or_folder.glob("*.tid")):
                self.convert_note(tid_file)

        # second pass: handle PascalCase links
        # https://tiddlywiki.com/static/Linking%2520in%2520WikiText.html
        self.handle_pascal_case_links()
