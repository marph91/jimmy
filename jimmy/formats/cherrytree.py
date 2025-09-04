"""Convert cherrytree notes to the intermediate format."""

import logging
from pathlib import Path
import re
import xml.etree.ElementTree as ET  # noqa: N817

from jimmy import common, converter, intermediate_format as imf
import jimmy.md_lib.common


LOGGER = logging.getLogger("jimmy")

LIST_RE = re.compile(r"^([^\S\r\n]*)(\d+)?(☐|☑|☒|•|◇|▪|▸|→|⇒|\)|-|>){1}", re.MULTILINE)
WHITESPACE_RE = re.compile(r"^(\s*)(.+?)(\s*)$")


def convert_table(node):
    table_md = jimmy.md_lib.common.MarkdownTable()
    for row_index, row in enumerate(node):
        assert row.tag == "row"
        columns = []
        for cell in row:
            assert cell.tag == "cell"
            cell_text = "" if cell.text is None else cell.text.replace("\n", "<br>")
            columns.append(cell_text)

        if row_index == 0:  # header row
            table_md.header_rows.append(columns)
        else:
            table_md.data_rows.append(columns)
    return table_md.create_md()


def list_sub_function(matchobj) -> str:  # pylint: disable=too-many-return-statements
    spaces, number, bullet = matchobj.groups()
    match bullet:
        # checklist
        case "☐":
            return spaces + "- [ ]"
        case "☑" | "☒":
            return spaces + "- [x]"
        # unnumbered list
        case "•" | "◇" | "▪" | "▸" | "→" | "⇒":
            return spaces + "-"
        # numbered list
        case ")" | "-" | ">":
            if number is None:
                return spaces + bullet
            return spaces + number + "."
    LOGGER.debug(f'Could not find list replacement for "{spaces, number, bullet}"')
    if number is None:
        return spaces + bullet
    return spaces + number + bullet


def fix_inline_formatting(md_content: str) -> str:
    r"""
    >>> fix_inline_formatting("☐ unchecked")
    '- [ ] unchecked'
    >>> fix_inline_formatting("☐ unchecked\n    ☒ nested checked")
    '- [ ] unchecked\n    - [x] nested checked'
    >>> fix_inline_formatting("dsa-dsa")
    'dsa-dsa'
    >>> fix_inline_formatting("☐4)")
    '- [ ]4)'
    >>> fix_inline_formatting("1) item\n    12- item\n\t145> item")
    '1. item\n    12. item\n\t145. item'
    """
    # horizontal line
    md_content = md_content.replace("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", "---")
    # lists
    md_content = LIST_RE.sub(list_sub_function, md_content)
    return md_content


def separate_whitespace(string: str) -> tuple[str, str, str]:
    # TODO: doctest
    match_ = WHITESPACE_RE.match(string)
    if match_ is None:
        return ("", string, "")
    # TODO: check types
    return match_.groups(default="")  # type: ignore[return-value]


def convert_rich_text(rich_text, heading_on_line: bool):
    if rich_text.text is None:
        return "", [], False
    if not rich_text.text.strip():
        return rich_text.text, [], False  # keep whitespaces but don't format them
    # TODO: is this fine with mixed text and child tags?
    note_links = []

    # formatting needs to be applied directly to the string without spaces
    leading, md_content, trailing = separate_whitespace(rich_text.text)
    for attrib, attrib_value in rich_text.attrib.items():
        match attrib:
            case "background" | "foreground" | "justification":
                pass  # not supported in markdown
            case "family":
                match attrib_value:
                    case "monospace":
                        if "\n" in md_content:  # multiline -> code block
                            md_content = f"\n```\n{md_content}\n```\n"
                        else:  # single line -> inline code
                            md_content = f"`{md_content}`"
                    case _:
                        LOGGER.debug(f"ignoring {attrib}={attrib_value}")
            case "link":
                url = attrib_value
                if url.startswith("webs "):
                    # web links
                    url = url.lstrip("webs ")
                    if rich_text.text == url:
                        md_content = f"<{md_content}>"
                    else:
                        md_content = f"[{md_content}]({url})"
                elif url.startswith("node "):
                    # internal node links
                    url = url.lstrip("node ")
                    text = md_content
                    md_content = f"[{text}]({url})"
                    # Split the note ID from the optional title. It can look like:
                    # "36 h2-3" or just "36".
                    # TODO: Anchors are not supported.
                    original_id = url.split(" ", maxsplit=1)[0]
                    note_links.append(imf.NoteLink(md_content, original_id, text))
                else:
                    # ?
                    md_content = f"[{md_content}]({url})"
            case "scale":
                match attrib_value:
                    case "sup":
                        md_content = f"^{md_content}^"
                    case "sub":
                        md_content = f"~{md_content}~"
                    case "h1" | "h2" | "h3" | "h4" | "h5" | "h6":
                        # This is an ugly hack to prevent multiple headings on one line.
                        # TODO: Avoid this by a list-based approach.
                        if not heading_on_line:
                            leading = f"{'#' * int(attrib_value[-1])} " + leading
                        heading_on_line = True
                    case _:
                        LOGGER.debug(f"ignoring {attrib}={attrib_value}")
            case "strikethrough":
                match attrib_value:
                    case "true":
                        md_content = f"~~{md_content}~~"
                    case _:
                        LOGGER.debug(f"ignoring {attrib}={attrib_value}")
            case "style":
                match attrib_value:
                    case "italic":
                        md_content = f"*{md_content}*"
                    case _:
                        LOGGER.debug(f"ignoring {attrib}={attrib_value}")
            case "underline":
                match attrib_value:
                    case "single":
                        md_content = f"++{md_content}++"
                    case _:
                        LOGGER.debug(f"ignoring {attrib}={attrib_value}")
            case "weight":
                match attrib_value:
                    case "heavy":
                        md_content = f"**{md_content}**"
                    case _:
                        LOGGER.debug(f"ignoring {attrib}={attrib_value}")
            case _:
                LOGGER.debug(f"ignoring {attrib}={attrib_value}")
    md_content = leading + md_content + trailing
    if not md_content:
        # TODO: make this more robust
        md_content = rich_text.text
    md_content = fix_inline_formatting(md_content)
    return md_content, note_links, heading_on_line and "\n" not in md_content


def convert_png(node, resource_folder) -> tuple[str, imf.Resource]:
    # It seems like the <encoded_png> attribute doesn't only cover PNG, but also
    # arbitrary attachments.

    # Keep the original filename and extension if possible.
    original_name = node.attrib.get("filename")

    # Use the original filename if possible.
    temp_filename = resource_folder / (
        common.unique_title() if original_name is None else original_name
    )
    temp_filename = common.write_base64(temp_filename, node.text)

    # assemble the markdown
    resource_md = f"![{temp_filename.name}]({temp_filename})"
    resource_imf = imf.Resource(temp_filename, resource_md, temp_filename.name)
    return resource_md + "\n", resource_imf


class Converter(converter.BaseConverter):
    accepted_extensions = [".ctd"]
    accept_folder = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bookmarked_nodes = []

    @common.catch_all_exceptions
    def convert_note(self, node, root_notebook: imf.Notebook):
        title = node.attrib.get("name", "")
        self.logger.debug(f'Converting note "{title}", parent "{root_notebook.title}"')
        note_imf = imf.Note(title, source_application=self.format)

        new_root_notebook = None  # only needed if there are sub notes
        note_body = ""
        heading_on_line = False  # True if there is a heading on the same line.
        for child in node:
            match child.tag:
                case "rich_text":
                    content_md, note_links_imf, heading_on_line = convert_rich_text(
                        child, heading_on_line
                    )
                    note_body += content_md
                    note_imf.note_links.extend(note_links_imf)
                case "node":
                    # there are sub notes -> create notebook with same name as note
                    if new_root_notebook is None:
                        new_root_notebook = imf.Notebook(title)
                        root_notebook.child_notebooks.append(new_root_notebook)
                    self.logger.debug(
                        f"new notebook: {new_root_notebook.title}, parent: {root_notebook.title}"
                    )
                    self.convert_note(child, new_root_notebook)
                case "codebox":
                    language = child.attrib.get("syntax_highlighting", "")
                    note_body += f"\n```{language}\n{child.text}\n```\n"
                case "encoded_png":
                    # Seems to be used for plaintext tex, too?!
                    if child.attrib.get("filename", "") == "__ct_special.tex":
                        note_body += f"\n```latex\n{child.text}\n```\n"
                        continue
                    if child.text is None and child.attrib.get("anchor"):
                        self.logger.debug(f"ignoring anchor {child.attrib.get('anchor')}")
                        continue
                    # We could handle resources here already,
                    # but we do it later with the common function.
                    resource_md, resource_imf = convert_png(child, self.root_path)
                    note_body += resource_md
                    note_imf.resources.append(resource_imf)
                case "table":
                    note_body += "\n" + convert_table(child) + "\n"
                case _:
                    self.logger.debug(f"ignoring tag {child.tag}")

        note_imf.body = note_body

        # cherrytree bookmark -> tag
        note_imf.original_id = node.attrib["unique_id"]
        if note_imf.original_id in self.bookmarked_nodes:
            note_imf.tags.append(imf.Tag("cherrytree-bookmarked"))
        if tags_str := node.attrib.get("tags", ""):
            note_imf.tags.extend(imf.Tag(t) for t in tags_str.strip().split(" ") if t.strip())

        if (created_time := node.attrib.get("ts_creation")) is not None:
            note_imf.created = common.timestamp_to_datetime(float(created_time))
        if (updated_time := node.attrib.get("ts_lastsave")) is not None:
            note_imf.updated = common.timestamp_to_datetime(float(updated_time))

        # If the cherrytree node is only used to contain children (i. e. a folder),
        # don't create a superfluous empty note.
        if not note_imf.is_empty():
            # Create the note below the notebook with the same name,
            # to stay compatible with the obsidian folder note plugins.
            # See: https://github.com/marph91/jimmy/issues/29
            parent_notebook = root_notebook if new_root_notebook is None else new_root_notebook
            parent_notebook.child_notes.append(note_imf)

    @common.catch_all_exceptions
    def convert_ctd(self, ctd_file: Path, parent_notebook: imf.Notebook):
        root_node = ET.parse(ctd_file).getroot()

        for child in root_node:
            match child.tag:
                case "bookmarks":
                    # We assume that bookmarks are defined before any nodes.
                    self.bookmarked_nodes = child.attrib.get("list", "").split(",")
                case "node":
                    self.convert_note(child, parent_notebook)
                case _:
                    self.logger.debug(f"ignoring tag {child.tag}")

    def convert(self, file_or_folder: Path):
        self.root_path = common.get_temp_folder()

        if file_or_folder.is_file():
            self.convert_ctd(file_or_folder, self.root_notebook)
        else:  # folder of .ctd
            for ctd_file in sorted(file_or_folder.glob("*.ctd")):
                title = ctd_file.stem
                self.logger.debug(f'Converting notebook "{title}"')
                parent_notebook = imf.Notebook(title)
                self.root_notebook.child_notebooks.append(parent_notebook)
                self.convert_ctd(ctd_file, parent_notebook)

        # Don't export empty notebooks
        self.remove_empty_notebooks()
