"""Convert tomboy-ng notes to the intermediate format."""

import datetime as dt
from pathlib import Path
import xml.etree.ElementTree as ET  # noqa: N817

import converter
import intermediate_format as imf


class Converter(converter.BaseConverter):
    accepted_extensions = [".note"]
    accept_folder = True

    def parse_content(self, node):
        # TODO
        # pylint: disable=too-many-branches

        # https://stackoverflow.com/a/26870728
        md_content = [node.text] if node.text is not None else []
        for child_index, child in enumerate(node):
            # match case doesn't work with fstrings
            if child.tag.endswith("bold"):
                md_content.append(f"**{child.text}**")
            elif child.tag.endswith("highlight"):
                md_content.append(child.text)  # TODO
            elif child.tag.endswith("italic"):
                md_content.append(f"*{child.text}*")
            elif child.tag.endswith("list"):
                for item in child:
                    if item.tag.endswith("list-item"):
                        md_content.append(f"- {item.text}")
                    else:
                        self.logger.warning(f"ignoring list tag {item.tag}")
            elif child.tag.endswith("monospace"):
                md_content.append(f"`{child.text}`")
            elif child.tag.endswith("strikeout"):
                md_content.append(f"~~{child.text}~~")
            elif child.tag.endswith("underline"):
                if child_index != 0:
                    # Don't put note title again in the note body.
                    md_content.append(f"++{child.text}++")
            elif (
                child.tag.endswith("small")
                or child.tag.endswith("large")
                or child.tag.endswith("huge")
            ):
                md_content.append(child.text)  # TODO
            else:
                self.logger.warning(f"ignoring tag {child.tag}")
            if child.tail is not None:
                md_content.append(child.tail)
        if node.tail is not None:
            md_content.append(node.tail)
        return "".join(md_content).strip()

    def convert_note(self, note_file: Path):
        # Format: https://wiki.gnome.org/Apps/Tomboy/NoteXmlFormat
        root_node = ET.parse(note_file).getroot()

        # There seems to be no simple solution of ignoring the namespace.
        # So we need to use the wildcard always: https://stackoverflow.com/q/13412496
        # TODO: are these tags or folders?
        tags_element = root_node.find("{*}tags")
        tags = []
        if tags_element is not None:
            tags = [
                tag.text
                for tag in tags_element.findall("{*}tag")
                if tag.text is not None
            ]
            if "system:template" in tags:
                return  # ignore templates

        content = root_node.find("{*}text/{*}note-content")
        body = self.parse_content(content)

        note_data = {"body": body}
        if (title := root_node.find("{*}title")) is not None:
            note_data["title"] = title.text
        else:
            note_data["title"] = body.split("\n", 1)[0]
        if (date_ := root_node.find("{*}create-date")) is not None:
            note_data["created"] = dt.datetime.fromisoformat(str(date_.text))
        if (date_ := root_node.find("{*}last-change-date")) is not None:
            note_data["updated"] = dt.datetime.fromisoformat(str(date_.text))
        self.root_notebook.child_notes.append(
            imf.Note(**note_data, tags=[imf.Tag(tag) for tag in tags])
        )

    def convert(self, file_or_folder: Path):
        if file_or_folder.is_dir():
            for note in file_or_folder.glob("*.note"):
                self.convert_note(note)
        else:
            self.convert_note(file_or_folder)
