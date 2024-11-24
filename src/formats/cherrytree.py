"""Convert cherrytree notes to the intermediate format."""

import base64
from pathlib import Path
import xml.etree.ElementTree as ET  # noqa: N817

import common
import converter
import intermediate_format as imf
import markdown_lib


def convert_table(node):
    table_md = markdown_lib.common.MarkdownTable()
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


def fix_inline_formatting(md_content: str) -> str:
    # horizontal line
    md_content = md_content.replace("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", "---")

    # TODO: make list replacements more robust
    # checklist
    md_content = md_content.replace("☐", "- [ ]")
    for checked_checkbox in ("☑", "☒"):
        md_content = md_content.replace(checked_checkbox, "- [x]")

    # unnumbered list
    for number in range(10):
        for bullet in (")", "-", ">"):
            md_content = md_content.replace(f"{number}{bullet}", f"{number}.")

    # unnumbered list
    for bullet in ("•", "◇", "▪", "→", "⇒"):
        md_content = md_content.replace(bullet, "-")
    return md_content


def convert_rich_text(rich_text, logger):
    # TODO: is this fine with mixed text and child tags?
    note_links = []
    md_content = ""
    for attrib, attrib_value in rich_text.attrib.items():
        match attrib:
            case "background" | "foreground" | "justification":
                if rich_text.text is not None:
                    md_content += rich_text.text
                logger.debug(
                    f"ignoring {attrib}={attrib_value} "
                    "as it's not supported in markdown"
                )
            case "family":
                match attrib_value:
                    case "monospace":
                        md_content = f"`{rich_text.text}`"
                    case _:
                        logger.warning(f"ignoring {attrib}={attrib_value}")
            case "link":
                url = attrib_value
                if url.startswith("webs "):
                    # web links
                    url = url.lstrip("webs ")
                    if rich_text.text == url:
                        md_content = f"<{url}>"
                    else:
                        md_content = f"[{rich_text.text}]({url})"
                elif url.startswith("node "):
                    # internal node links
                    url = url.lstrip("node ")
                    md_content = f"[{rich_text.text}]({url})"
                    # Split the note ID from the optional title. It can look like:
                    # "36 h2-3" or just "36".
                    # TODO: Anchors are not supported.
                    original_id = url.split(" ", maxsplit=1)[0]
                    note_links.append(imf.NoteLink(md_content, original_id, rich_text.text))
                else:
                    # ?
                    md_content = f"[{rich_text.text}]({url})"
            case "scale":
                match attrib_value:
                    case "sup":
                        md_content = f"^{rich_text.text}^"
                    case "sub":
                        md_content = f"~{rich_text.text}~"
                    case "h1":
                        md_content = f"# {rich_text.text}"
                    case "h2":
                        md_content = f"## {rich_text.text}"
                    case "h3":
                        md_content = f"### {rich_text.text}"
                    case "h4":
                        md_content = f"#### {rich_text.text}"
                    case "h5":
                        md_content = f"##### {rich_text.text}"
                    case "h6":
                        md_content = f"###### {rich_text.text}"
                    case _:
                        logger.warning(f"ignoring {attrib}={attrib_value}")
            case "strikethrough":
                match attrib_value:
                    case "true":
                        md_content = f"~~{rich_text.text}~~"
                    case _:
                        logger.warning(f"ignoring {attrib}={attrib_value}")
            case "style":
                match attrib_value:
                    case "italic":
                        md_content = f"*{rich_text.text}*"
                    case _:
                        logger.warning(f"ignoring {attrib}={attrib_value}")
            case "underline":
                match attrib_value:
                    case "single":
                        md_content = f"++{rich_text.text}++"
                    case _:
                        logger.warning(f"ignoring {attrib}={attrib_value}")
            case "weight":
                match attrib_value:
                    case "heavy":
                        md_content = f"**{rich_text.text}**"
                    case _:
                        logger.warning(f"ignoring {attrib}={attrib_value}")
            case _:
                logger.warning(f"ignoring {attrib}={attrib_value}")
    if not md_content:
        # TODO: make this more robust
        md_content += "" if rich_text.text is None else rich_text.text
    if not rich_text.attrib:
        # TODO: make this more robust
        # Make sure to don't break links.
        md_content = fix_inline_formatting(md_content)
    return md_content, note_links


def convert_png(node, resource_folder) -> tuple[str, imf.Resource]:
    # It seems like the <encoded_png> attribute doesn't only cover PNG, but also
    # arbitrary attachments.

    # Keep the original filename and extension if possible.
    original_name = node.attrib.get("filename")

    # Use the original filename if possible.
    # TODO: Files with same name are replaced.
    temp_filename = resource_folder / (
        common.unique_title() if original_name is None else original_name
    )
    temp_filename.write_bytes(base64.b64decode(node.text))

    # assemble the markdown
    resource_md = f"![{temp_filename.name}]({temp_filename})"
    resource_imf = imf.Resource(temp_filename, resource_md, temp_filename.name)
    return resource_md + "\n", resource_imf


class Converter(converter.BaseConverter):
    accepted_extensions = [".ctd"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bookmarked_nodes = []

    def convert_to_markdown(self, node, root_notebook):
        # TODO
        # pylint: disable=too-many-locals
        title = node.attrib.get("name", "")
        self.logger.debug(f'Converting note "{title}", parent "{root_notebook.title}"')
        note_imf = imf.Note(title, source_application=self.format)

        new_root_notebook = None  # only needed if there are sub notes
        note_body = ""
        for child in node:
            match child.tag:
                case "rich_text":
                    content_md, note_links_imf = convert_rich_text(child, self.logger)
                    note_body += content_md
                    note_imf.note_links.extend(note_links_imf)
                case "node":
                    # there are sub notes -> create notebook with same name as note
                    if new_root_notebook is None:
                        new_root_notebook = imf.Notebook(title)
                        root_notebook.child_notebooks.append(new_root_notebook)
                    self.logger.debug(
                        f"new notebook: {new_root_notebook.title}, "
                        f"parent: {root_notebook.title}"
                    )
                    self.convert_to_markdown(child, new_root_notebook)
                case "codebox":
                    language = child.attrib.get("syntax_highlighting", "")
                    note_body += f"\n```{language}\n{child.text}\n```\n"
                case "encoded_png":
                    # Seems to be used for plaintext tex, too?!
                    if child.attrib.get("filename", "") == "__ct_special.tex":
                        note_body += f"\n```latex\n{child.text}\n```\n"
                        continue
                    if child.text is None and child.attrib.get("anchor"):
                        self.logger.debug(
                            f"ignoring anchor {child.attrib.get('anchor')}"
                        )
                        continue
                    # We could handle resources here already,
                    # but we do it later with the common function.
                    resource_md, resource_imf = convert_png(child, self.root_path)
                    note_body += resource_md
                    note_imf.resources.append(resource_imf)
                case "table":
                    note_body += convert_table(child)
                case _:
                    self.logger.warning(f"ignoring tag {child.tag}")

        note_imf.body = note_body

        # cherrytree bookmark -> tag
        note_imf.original_id = node.attrib["unique_id"]
        if note_imf.original_id in self.bookmarked_nodes:
            note_imf.tags.append(imf.Tag("cherrytree-bookmarked"))
        if tags_str := node.attrib.get("tags", ""):
            note_imf.tags.extend(
                imf.Tag(t) for t in tags_str.strip().split(" ") if t.strip()
            )

        if (created_time := node.attrib.get("ts_creation")) is not None:
            note_imf.created = common.timestamp_to_datetime(int(created_time))
        if (updated_time := node.attrib.get("ts_lastsave")) is not None:
            note_imf.updated = common.timestamp_to_datetime(int(updated_time))

        # If the cherrytree node is only used to contain children (i. e. a folder),
        # don't create a superfluous empty note.
        if not note_imf.is_empty():
            root_notebook.child_notes.append(note_imf)

    def convert(self, file_or_folder: Path):
        self.root_path = common.get_temp_folder()
        root_node = ET.parse(file_or_folder).getroot()

        for child in root_node:
            match child.tag:
                case "bookmarks":
                    # We assume that bookmarks are defined before any nodes.
                    self.bookmarked_nodes = child.attrib.get("list", "").split(",")
                case "node":
                    self.convert_to_markdown(child, self.root_notebook)
                case _:
                    self.logger.warning(f"ignoring tag {child.tag}")

        # Don't export empty notebooks
        self.remove_empty_notebooks()
