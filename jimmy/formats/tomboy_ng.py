"""Convert tomboy-ng notes to the intermediate format."""

from pathlib import Path
import xml.etree.ElementTree as ET  # noqa: N817

from jimmy import common, converter, intermediate_format as imf


class Converter(converter.BaseConverter):
    def parse_content(self, node):
        note_links = []

        # https://stackoverflow.com/a/26870728
        md_content = [node.text] if node.text is not None else []
        for child_index, child in enumerate(node):
            # match case doesn't work with fstrings
            if (
                child.tag.endswith("bold")
                or child.tag.endswith("large")
                or child.tag.endswith("huge")
            ):
                md_content.append(f"**{child.text}**")
            elif child.tag.endswith("highlight"):
                md_content.append(f"=={child.text}==")
            elif child.tag.endswith("italic"):
                md_content.append(f"*{child.text}*")
            elif child.tag.endswith("list"):
                for item in child:
                    if item.tag.endswith("list-item"):
                        md_content.append(f"- {item.text}")
                    else:
                        self.logger.debug(f"ignoring list tag {item.tag}")
            elif child.tag.endswith("monospace"):
                md_content.append(f"`{child.text}`")
            elif child.tag.endswith("strikeout"):
                md_content.append(f"~~{child.text}~~")
            elif child.tag.endswith("underline"):
                if child_index != 0:
                    # Don't put note title again in the note body.
                    md_content.append(f"++{child.text}++")
            elif child.tag.endswith("small"):
                # There is no <small> in Markdown. Keep the text only.
                # https://blog.markdowntools.com/posts/small-text-in-markdown
                md_content.append(child.text)
            elif child.tag.endswith("internal"):
                # Just some arbitrary format. It gets replaced later.
                md_content.append(f"[[{child.text}]]")
                note_links.append(imf.NoteLink(f"[[{child.text}]]", child.text, child.text))
            else:
                self.logger.debug(f"ignoring tag {child.tag}")
            if child.tail is not None:
                md_content.append(child.tail)
        if node.tail is not None:
            md_content.append(node.tail)
        return "".join(md_content).strip(), note_links

    @common.catch_all_exceptions
    def convert_note(self, note_file: Path):
        # Format: https://wiki.gnome.org/Apps/Tomboy/NoteXmlFormat
        root_node = ET.parse(note_file).getroot()

        # There seems to be no simple solution of ignoring the namespace.
        # So we need to use the wildcard always: https://stackoverflow.com/q/13412496
        # TODO: are these tags or folders?
        tags_element = root_node.find("{*}tags")
        tags = []
        if tags_element is not None:
            tags = [tag.text for tag in tags_element.findall("{*}tag") if tag.text is not None]
            if "system:template" in tags:
                return  # ignore templates

        content = root_node.find("{*}text/{*}note-content")
        body, note_links = self.parse_content(content)

        if (note_title := root_node.find("{*}title")) is not None and note_title.text is not None:
            title = note_title.text
        else:
            title = body.split("\n", maxsplit=1)[0]
        self.logger.debug(f'Converting note "{title}"')
        note_imf = imf.Note(title, body, tags=[imf.Tag(tag) for tag in tags], note_links=note_links)
        if (date_ := root_node.find("{*}create-date")) is not None:
            note_imf.created = common.iso_to_datetime(str(date_.text))
        if (date_ := root_node.find("{*}last-change-date")) is not None:
            note_imf.updated = common.iso_to_datetime(str(date_.text))
        self.root_notebook.child_notes.append(note_imf)

    def convert(self, file_or_folder: Path):
        if file_or_folder.is_dir():
            notes = list(file_or_folder.glob("*.note"))
            if len(notes) == 0:
                self.logger.warning("Couldn't find a note file. Is this really a tomboy ng export?")
                return
            for note in sorted(notes):
                self.convert_note(note)
        else:
            self.convert_note(file_or_folder)
