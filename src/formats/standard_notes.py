"""Convert Standard Notes notes to the intermediate format."""

from collections import defaultdict
import datetime as dt
import enum
import logging
import json
from pathlib import Path

import converter
import intermediate_format as imf
import markdown_lib.common
import common

LOGGER = logging.getLogger("jimmy")


class Format(enum.Flag):
    """
    Represents a super text format:
    https://github.com/standardnotes/app/blob/5c23a11b5a4555e809ecc7ca7775e49bc0ccda0f/packages/web/src/javascripts/Components/SuperEditor/Lexical/Utils/MarkdownExport.ts#L10
    https://github.com/facebook/lexical/blob/fe4f5b8cb408476f39d6689ae8886be1d1322df1/packages/lexical/src/LexicalConstants.ts#L38-L46
    """

    BOLD = 1
    ITALIC = 1 << 1
    STRIKETHROUGH = 1 << 2
    UNDERLINE = 1 << 3
    CODE = 1 << 4
    SUBSCRIPT = 1 << 5
    SUPERSCRIPT = 1 << 6
    HIGHLIGHT = 1 << 7


def format_text(text: str, format_: Format) -> str:
    for item in Format:
        if item in format_:
            match item:
                case Format.BOLD:
                    text = f"**{text}**"
                case Format.ITALIC:
                    text = f"*{text}*"
                case Format.STRIKETHROUGH:
                    text = f"~~{text}~~"
                case Format.UNDERLINE:
                    text = f"++{text}++"
                case Format.CODE:
                    text = f"`{text}`"
                case Format.SUBSCRIPT:
                    text = f"~{text}~"
                case Format.SUPERSCRIPT:
                    text = f"^{text}^"
                case Format.HIGHLIGHT:
                    text = f"=={text}=="
                case _:
                    LOGGER.debug(f"Unknown format: {item}")
    return text


class SuperToMarkdown:
    def __init__(self):
        self.last_list = None
        self.md = []

    def add_newlines(self, count: int):
        """Add as many newlines as needed. Consider preceding newlines."""
        # TODO: check for simpler implementation
        if not self.md:
            return
        # how many newlines are at the end already?
        index = 0
        while index < len(self.md) and index < count and self.md[-index - 1] == "\n":
            index += 1
        # insert missing newlines
        if index > 0:
            self.md[-index:] = ["\n"] * count
        else:
            self.md.extend(["\n"] * count)

    def add_text(self, text: str | list[str], quote_level: int):
        if not text:
            return
        if isinstance(text, str):
            text = [text]
        if quote_level == 0:
            self.md.extend(text)
            return
        if self.md and self.md[-1] == "\n":
            self.md.append("> " * quote_level)
        for item in text:
            self.md.append(item)
            if item == "\n":
                self.md.append("> " * quote_level)

    def parse_table(self, block: dict):
        md_before = self.md
        table = markdown_lib.common.MarkdownTable()
        for row in block["children"]:
            # assert row["type"] == "tablerow"
            row_cells = []
            is_header_row = False
            for cell in row["children"]:
                # assert cell["type"] == "tablecell"
                if cell["headerState"] == 1 and not table.header_rows:
                    is_header_row = True
                self.md = []
                self.parse_block(cell)
                # newlines aren't allowed in Markdown tables
                row_cells.extend([md for md in self.md if md != "\n"])
            if is_header_row:
                table.header_rows.append(row_cells)
            else:
                table.data_rows.append(row_cells)
        self.md = md_before
        self.add_text(table.create_md(), 0)

    def parse_block(self, block: dict, quote_level: int = 0):
        # TODO: "indent" is ignored
        # https://stackoverflow.com/a/6046472/7410886
        # assert block["version"] == 1
        newlines = 0
        append = []
        skip_children = False
        match block["type"]:
            case "autolink" | "link":
                link = markdown_lib.common.MarkdownLink(
                    block["children"][0].get("text", ""),
                    block.get("url", ""),
                    "" if (title := block.get("title")) is None else title,
                )
                self.add_text(link.reformat(), quote_level)
                skip_children = True
            case "code":
                self.add_text([f"```{block.get('language', '')}", "\n"], quote_level)
                newlines = 1
                append = ["```", "\n", "\n"]
            case "collapsible-container":
                # There is no collapse in Markdown.
                # Convert it to bold (collapsible-title) + text (collapsible-content).
                pass
            case "collapsible-title":
                self.add_text(f"**{block['children'][0]['text']}**", quote_level)
                skip_children = True
                newlines = 2
            case "collapsible-content":
                pass
                # self.add_text(block["text"], quote_level)
                # newlines = 2
            case "heading":
                self.add_text(f"{'#' * int(block['tag'][-1])} ", quote_level)
                newlines = 2
            case "horizontalrule":
                self.add_newlines(2)
                self.add_text("---", quote_level)
                newlines = 2
            case "linebreak":
                self.add_newlines(1)
            case "list":
                # TODO: nested list
                self.last_list = block["listType"]
                newlines = 2
            case "listitem":
                # TODO: indent
                match self.last_list:
                    case "bullet":
                        bullet = "- "
                    case "number":
                        bullet = "1. "
                    case "check":
                        bullet = "- [x] " if block.get("checked", False) else "- [ ] "
                self.add_text(bullet, quote_level)
                newlines = 1
            case "paragraph":
                self.add_newlines(1)
                newlines = 2
            case "root":
                pass
            case "snfile":
                # TODO: Is the uuid relevant for note links?
                # print("snfile", block["version"], block["fileUuid"])
                pass
            case "table":
                self.add_newlines(2)
                self.parse_table(block)
                newlines = 2
                skip_children = True
            case "tablerow" | "tablecell":
                pass  # handled in parse_table()
            case "code-highlight" | "text":
                self.add_text(
                    format_text(block["text"], Format(block["format"])), quote_level
                )
            case "quote":
                quote_level += 1
                newlines = 2
            case _:
                LOGGER.debug(f"Unknown block type: {block['type']}")
        if not skip_children:
            for child in block.get("children", []):
                self.parse_block(child, quote_level)
        self.add_newlines(newlines)
        self.add_text(append, quote_level)

    def convert(self, super_json: str) -> str:
        super_dict = json.loads(super_json)
        self.md = []
        self.parse_block(super_dict["root"])
        return "".join(self.md)


class Converter(converter.BaseConverter):
    accepted_extensions = [".zip"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.note_id_tag_map = defaultdict(list)
        self.archive_notebook = imf.Notebook("Archive")
        self.trash_notebook = imf.Notebook("Trash")

    @common.catch_all_exceptions
    def convert_note(self, item: dict):
        title = item["content"].get("title", common.unique_title())
        self.logger.debug(f'Converting note "{title}"')
        note_imf = imf.Note(
            title,
            created=dt.datetime.fromisoformat(item["created_at"]),
            updated=dt.datetime.fromisoformat(item["updated_at"]),
            source_application=self.format,
            original_id=item["uuid"],
        )

        note_imf.tags.extend(self.note_id_tag_map.get(item["uuid"], []))
        if item["content"].get("starred", False):
            note_imf.tags.append(imf.Tag("standard_notes-starred"))

        match item["content"].get("noteType", "plain-text"):
            case "plain-text":
                note_imf.body = item["content"]["text"]
            case "super":
                if body := item["content"]["text"]:
                    super_converter = SuperToMarkdown()
                    note_imf.body = super_converter.convert(body)
                else:
                    note_imf.body = ""

            case _:
                note_imf.body = item["content"]["text"]
                self.logger.debug(
                    f'Unsupported note type "{item["content"]["noteType"]}"'
                )

        if item["content"].get("trashed", False):
            parent = self.trash_notebook
        elif item["content"]["appData"]["org.standardnotes.sn"].get("archived", False):
            parent = self.archive_notebook
        else:
            parent = self.root_notebook
        parent.child_notes.append(note_imf)

    def convert(self, file_or_folder: Path):
        target_file = None
        for file_ in [
            "Standard Notes Backup and Import File.txt",
            "Standard Notes Backup and Import File txt.txt",
        ]:
            if (self.root_path / file_).is_file():
                target_file = self.root_path / file_
                break
        if target_file is None:
            self.logger.error("Couldn't find text file in zip.")
            return

        input_json = json.loads(target_file.read_text(encoding="utf-8"))

        # first pass: get all tags
        # In the export, notes are assigned to tags. We need tags assigned to notes.
        for item in input_json["items"]:
            if item["content_type"] != "Tag" or item.get("deleted", False):
                continue
            tag = imf.Tag(
                item["content"]["title"],
                original_id=item["uuid"],
            )
            for reference in item["content"]["references"]:
                if uuid := reference.get("uuid"):
                    self.note_id_tag_map[uuid].append(tag)

        self.root_notebook.child_notebooks.extend(
            [self.archive_notebook, self.trash_notebook]
        )

        # second pass: get all notes and assign tags to notes
        for item in input_json["items"]:
            if item["content_type"] != "Note" or item.get("deleted", False):
                continue
            self.convert_note(item)

        # Don't export empty notebooks
        self.remove_empty_notebooks()
