"""Convert Zettelkasten notes to the intermediate format."""

import datetime as dt
from pathlib import Path
import xml.etree.ElementTree as ET  # noqa: N817

import common
import converter
import intermediate_format as imf


class Converter(converter.BaseConverter):
    accepted_extensions = [".zkn3"]

    def prepare_input(self, input_: Path) -> Path:
        return common.extract_zip(input_)

    def parse_attributes(self, zettel, note_imf: imf.Note):
        for key, value in zettel.attrib.items():
            match key:
                case "zknid":
                    note_imf.original_id = value
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
        self.root_path = self.prepare_input(file_or_folder)

        attachments_folder = file_or_folder.parent / "attachments"
        attachments_available = attachments_folder.is_dir()
        if not attachments_available:
            self.logger.warning(
                f"No attachments folder found at {attachments_folder}. "
                "Attachments are not converted."
            )

        tag_id_name_map = {}
        root_node = ET.parse(self.root_path / "keywordFile.xml").getroot()
        for keyword in root_node.findall("entry"):
            if (tag_id := keyword.attrib.get("f")) is not None:
                tag_id_name_map[tag_id] = keyword.text

        root_node = ET.parse(self.root_path / "zknFile.xml").getroot()
        for zettel in root_node.findall("zettel"):
            title = item.text if (item := zettel.find("title")) is not None else ""
            assert title is not None
            self.logger.debug(f'Converting note "{title}"')
            note_imf = imf.Note(title)

            self.parse_attributes(zettel, note_imf)

            for item in zettel:
                match item.tag:
                    case "title":
                        pass  # handled already
                    case "content":
                        note_imf.body = item.text if item.text else ""
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
