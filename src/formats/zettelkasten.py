"""Convert Zettelkasten notes to the intermediate format."""

import datetime as dt
from pathlib import Path
import xml.etree.ElementTree as ET  # noqa: N817

import bbcode

import common
import converter
import intermediate_format as imf


def bbcode_to_markdown(
    bbcode_str: str,
) -> tuple[str, list[imf.NoteLink], list[imf.Resource]]:
    # pylint: disable=unused-argument
    note_links = []
    images = []

    parser = bbcode.Parser()
    parser.add_simple_formatter("h1", "# %(value)s")
    parser.add_simple_formatter("h2", "## %(value)s")
    parser.add_simple_formatter("br", "\n", standalone=True)
    parser.add_simple_formatter("q", "> %(value)s")
    parser.add_simple_formatter("code", "\n```\n%(value)s\n```")

    # left, right aligned, centered, justified - not supported
    parser.add_simple_formatter("al", "%(value)s")
    parser.add_simple_formatter("ar", "%(value)s")
    parser.add_simple_formatter("c", "%(value)s")
    parser.add_simple_formatter("ab", "%(value)s")

    # text formatting
    parser.add_simple_formatter("f", "**%(value)s**")
    parser.add_simple_formatter("k", "*%(value)s*")
    parser.add_simple_formatter("u", "++%(value)s++")
    parser.add_simple_formatter("d", "~~%(value)s~~")
    parser.add_simple_formatter("qm", '"%(value)s"')
    parser.add_simple_formatter("sub", "~%(value)s~")
    parser.add_simple_formatter("sup", "^%(value)s^")

    # colored -> bold
    parser.add_simple_formatter("h", "**%(value)s**")

    # forms
    def _render_form(name, value, options, parent, context):
        return " ".join([f"`{key}={value}`" for key, value in options.items()])

    parser.add_formatter("form", _render_form, standalone=True)

    # lists
    def _render_list_item(name, value, options, parent, context):
        match parent.tag_name:
            case "l":
                return f"* {value}\n"
            case "n":
                return f"1. {value}\n"
            case _:
                return value

    parser.add_simple_formatter("l", "%(value)s")
    parser.add_simple_formatter("n", "%(value)s")
    parser.add_formatter("*", _render_list_item)

    # images and internal note links
    def _render_image(name, value, options, parent, context):
        text = f"![]({value})"
        images.append(imf.Resource(Path(value), text))
        return text

    parser.add_formatter("img", _render_image)

    def _render_internal_link(name, value, options, parent, context):
        id_ = list(options)[0]
        text = f"[{value}]({id_})"
        note_links.append(imf.NoteLink(text, id_, value))
        return text

    parser.add_formatter("z", _render_internal_link)

    # tables
    def _render_table(name, value, options, parent, context):
        table_md = []
        for line in value.split("\n"):
            if "^" in line:
                # header
                table_md.append("| " + " | ".join(line.split("^")) + " |")
                separator = ["---"] * len(line.split("^"))
                table_md.append("| " + " | ".join(separator) + " |")
            elif "|" in line:
                # row
                table_md.append("| " + " | ".join(line.split("|")) + " |")
            else:
                table_md.append(line)
        return "\n".join(table_md)

    parser.add_formatter("table", _render_table)
    parser.add_simple_formatter("tc", "%(value)s\n")

    markdown = parser.format(
        bbcode_str,
        install_defaults=False,
        escape_html=False,
        newline="\n",
        replace_cosmetic=False,
        replace_links=False,
    )
    return markdown, note_links, images


class Converter(converter.BaseConverter):
    accepted_extensions = [".zkn3"]

    def prepare_input(self, input_: Path) -> Path:
        return common.extract_zip(input_)

    def parse_attributes(self, zettel, note_imf: imf.Note):
        for key, value in zettel.attrib.items():
            match key:
                case "zknid":
                    pass  # This ID seems to be not used for linking.
                case "ts_created":
                    note_imf.created = dt.datetime.strptime(value, "%y%m%d%H%M")
                case "ts_edited":
                    note_imf.updated = dt.datetime.strptime(value, "%y%m%d%H%M")
                case "rating" | "ratingcount":
                    # TODO: add when arbitrary metadata is supported
                    pass
                case _:
                    self.logger.warning(f"ignoring attribute {key}={value}")

    def convert(self, file_or_folder: Path):
        # TODO
        # pylint: disable=too-many-branches,too-many-locals
        self.root_path = self.prepare_input(file_or_folder)

        attachments_folder = file_or_folder.parent / "attachments"
        attachments_available = attachments_folder.is_dir()
        if not attachments_available:
            self.logger.warning(
                f"No attachments folder found at {attachments_folder}. "
                "Attachments are not converted."
            )

        images_folder = file_or_folder.parent / "img"
        images_available = images_folder.is_dir()
        if not images_available:
            self.logger.warning(
                f"No images folder found at {images_folder}. "
                "Images are not converted."
            )

        tag_id_name_map = {}
        root_node = ET.parse(self.root_path / "keywordFile.xml").getroot()
        for keyword in root_node.findall("entry"):
            if (tag_id := keyword.attrib.get("f")) is not None:
                tag_id_name_map[tag_id] = keyword.text

        root_node = ET.parse(self.root_path / "zknFile.xml").getroot()
        for id_, zettel in enumerate(root_node.findall("zettel"), start=1):
            title = item.text if (item := zettel.find("title")) is not None else ""
            assert title is not None
            self.logger.debug(f'Converting note "{title}"')
            note_imf = imf.Note(title, original_id=str(id_))

            self.parse_attributes(zettel, note_imf)

            for item in zettel:
                match item.tag:
                    case "title":
                        pass  # handled already
                    case "content":
                        body, note_links, images = bbcode_to_markdown(
                            item.text if item.text else ""
                        )
                        note_imf.body = body
                        note_imf.note_links.extend(note_links)

                        if images_available:
                            for image in images:
                                image.filename = images_folder / image.filename
                                # Set manually, because with invalid path it's
                                # set to False.
                                image.is_image = True
                                note_imf.resources.append(image)
                    case "author":
                        note_imf.author = item.text
                    case "keywords":
                        if item.text is not None:
                            for tag_id in item.text.split(","):
                                tag_name = tag_id_name_map.get(tag_id, tag_id)
                                assert tag_name is not None
                                note_imf.tags.append(imf.Tag(tag_name))
                    case "links":
                        if not attachments_available:
                            continue
                        # links = resources are always attached at the end
                        for link in item.findall("link"):
                            if link.text is None:
                                continue
                            note_imf.resources.append(
                                imf.Resource(attachments_folder / link.text)
                            )
                    case "luhmann" | "misc" | "zettel":
                        pass  # always None
                    case "manlinks":
                        pass  # TODO: Should correspond to the parsed note links.
                    case _:
                        self.logger.warning(f"ignoring item {item.tag}={item.text}")
            self.root_notebook.child_notes.append(note_imf)