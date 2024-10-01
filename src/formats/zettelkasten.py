"""Convert Zettelkasten (zkn3) notes to the intermediate format."""

import datetime as dt
from pathlib import Path
import xml.etree.ElementTree as ET  # noqa: N817

import converter
import intermediate_format as imf
import markdown_lib.common
from markdown_lib.zettelkasten import bbcode_to_md


class Converter(converter.BaseConverter):
    accepted_extensions = [".zkn3"]

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

    def handle_markdown_links(self, body, source_folder) -> tuple[list, list]:
        note_links = []
        resources = []
        for link in markdown_lib.common.get_markdown_links(body):
            if link.is_web_link or link.is_mail_link:
                continue  # keep the original links
            if link.url.startswith("note://"):
                original_id = link.url.replace("note://", "")
                note_links.append(imf.NoteLink(str(link), original_id, link.text))
            elif link.is_image:
                resources.append(
                    imf.Resource(source_folder / "img" / link.url, str(link), link.text)
                )
            else:
                resources.append(
                    imf.Resource(
                        source_folder / "attachments" / link.url, str(link), link.text
                    )
                )
        return resources, note_links

    def convert(self, file_or_folder: Path):
        # TODO
        # pylint: disable=too-many-branches,too-many-locals
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
                        body = bbcode_to_md(item.text if item.text else "")
                        note_imf.body = body
                        resources, note_links = self.handle_markdown_links(
                            body, file_or_folder.parent
                        )
                        note_imf.resources.extend(resources)
                        note_imf.note_links.extend(note_links)

                        # if images_available:
                        #     for image in images:
                        #         image.filename = images_folder / image.filename
                        #         # Set manually, because with invalid path it's
                        #         # set to False.
                        #         image.is_image = True
                        #         note_imf.resources.extend(resources)
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
                    case "luhmann":  # folgezettel
                        if item.text is None:
                            continue
                        # TODO: Ensure that this is called always
                        # after the initial note content is parsed.
                        sequences = []
                        for note_id in item.text.split(","):
                            text = f"[{note_id}]({note_id})"
                            sequences.append(text)
                            note_imf.note_links.append(
                                imf.NoteLink(text, note_id, note_id)
                            )
                        note_imf.body += (
                            "\n\n## Note Sequences\n\n" + ", ".join(sequences) + "\n"
                        )
                    case "misc" | "zettel":
                        pass  # always None
                    case "manlinks":
                        pass  # TODO: Should correspond to the parsed note links.
                    case _:
                        self.logger.warning(f"ignoring item {item.tag}={item.text}")
            self.root_notebook.child_notes.append(note_imf)
