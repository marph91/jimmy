"""Convert Zettelkasten (zkn3) notes to the intermediate format."""

import datetime as dt
from pathlib import Path
import re
import xml.etree.ElementTree as ET  # noqa: N817

import pyparsing as pp

import common
import converter
import intermediate_format as imf


# Prevent spaces, tabs and newlines from being stripped.
pp.ParserElement.set_default_whitespace_chars("")


colored_re = re.compile(r"\[h .*\](.*?)\[\/h\]")
internal_link_re = re.compile(r"\[z (\d+)\](.*?)\[\/z\]")
table_re = re.compile(r"\[table\](\[tc\](.*?)\[\/tc\])?([\S\s]*?)\[\/table\]")
# hacky, but works for now
list_re = re.compile(r"\[([ln])\]\[\*\](.*?)\[\/\*\]\[\/[ln]\]")


def tag(source_tag, target_tag, replace_first_only=False):
    """Conversion of a quoted string. I. e. with the same start and end tags."""

    def to_md(_, t):  # noqa
        if replace_first_only:
            return target_tag + t[0]
        return target_tag + t[0] + target_tag

    return pp.QuotedString(
        f"[{source_tag}]", end_quote_char=f"[/{source_tag}]"
    ).set_parse_action(to_md)


def newline():
    return pp.Literal("[br]").set_parse_action(lambda: "\n")


def colored():
    # colored -> bold
    def to_md(_, t):  # noqa
        return "**" + t[0][0] + "**"

    return pp.Regex(colored_re, as_group_list=True).set_parse_action(to_md)


def code_block():
    def to_md(_, t):  # noqa
        return f"\n```\n{t[0]}\n```"

    return pp.QuotedString(
        "[code]", end_quote_char="[/code]", multiline=True
    ).set_parse_action(to_md)


def list_():
    def to_md(_, t):  # noqa
        type_, content = t[0]
        list_character = {"l": "*", "n": "1."}[type_]
        return (
            f"{list_character} "
            + f"\n{list_character} ".join(content.split("[/*][*]"))
            + "\n"
        )

    return pp.Regex(list_re, as_group_list=True).set_parse_action(to_md)


def image():
    def to_md(_, t):  # noqa
        return f"![{t[0]}]({t[0]})"

    return pp.QuotedString("[img]", end_quote_char="[/img]").set_parse_action(to_md)


def internal_link():
    def to_md(_, t):  # noqa
        id_, title = t[0]
        return f"[{title}](note://{id_})"

    return pp.Regex(internal_link_re, as_group_list=True).set_parse_action(to_md)


def table():
    def to_md(_, t):  # noqa
        _, caption, content = t[0]

        table_md = common.MarkdownTable()
        if caption is not None:
            table_md.caption = caption

        for line in content.split("\n"):
            if not line.strip():
                continue
            if "^" in line:
                table_md.header_rows.append(line.split("^"))
            else:
                table_md.data_rows.append(line.split("|"))
        return table_md.create_md()

    return pp.Regex(table_re, as_group_list=True).set_parse_action(to_md)


def bbcode_to_md(wikitext: str) -> str:
    r"""
    Main bbcode to Markdown conversion function.

    # hyperlinks are markdown already

    >>> bbcode_to_md("[f]fett[/f]")
    '**fett**'
    >>> bbcode_to_md("das ist [d]durchgestrichener[/d] text")
    'das ist ~~durchgestrichener~~ text'
    >>> bbcode_to_md("[h #ffff00]colored[/h] text")
    '**colored** text'
    >>> bbcode_to_md("[h3]heading 3[/h3]")
    '### heading 3'
    >>> bbcode_to_md("some[br]li nes[br]he re")
    'some\nli nes\nhe re'
    >>> bbcode_to_md("[q]single line quote[/q]")
    '> single line quote'
    >>> bbcode_to_md("disappearing [al]tag[/al]")
    'disappearing tag'
    >>> bbcode_to_md("[code]some code[/code]")
    '\n```\nsome code\n```'
    >>> bbcode_to_md("[code]long[br]code block[/code]")
    '\n```\nlong\ncode block\n```'
    >>> bbcode_to_md("[img]some image.png[/img]")
    '![some image.png](some image.png)'
    >>> bbcode_to_md("link [z 3]zu Zettel 3[/z]")
    'link [zu Zettel 3](note://3)'
    >>> bbcode_to_md("[table][tc]Test Table[/tc][br]h 1^h 2^h3[br]d1 |d 2 |d3[/table]")
    'Test Table\n\n| h 1 | h 2 | h3 |\n| --- | --- | --- |\n| d1  | d 2  | d3 |\n'
    >>> bbcode_to_md("[table]h 1^h 2^h3[br]d1 |d 2 |d3[/table]")
    '| h 1 | h 2 | h3 |\n| --- | --- | --- |\n| d1  | d 2  | d3 |\n'
    >>> bbcode_to_md("[l][*]Here an item[/*][*]Other item![/*][/l]")
    '* Here an item\n* Other item!\n'
    >>> bbcode_to_md("[n][*]Numbered item[/*][*]Other numbered item![/*][/n]")
    '1. Numbered item\n1. Other numbered item!\n'
    """
    bbcode_markup = (
        newline()
        # text formatting
        | tag("f", "**")
        | tag("k", "*")
        | tag("u", "++")
        | tag("d", "~~")
        | tag("qm", '"')
        | tag("sub", "~")
        | tag("sup", "^")
        | colored()
        # left, right aligned, centered, justified - not supported
        | tag("al", "")
        | tag("ar", "")
        | tag("c", "")
        | tag("ab", "")
        #
        | tag("h1", "# ", replace_first_only=True)
        | tag("h2", "## ", replace_first_only=True)
        | tag("h3", "### ", replace_first_only=True)
        | tag("h4", "#### ", replace_first_only=True)
        | tag("h5", "##### ", replace_first_only=True)
        | tag("h6", "###### ", replace_first_only=True)
        | tag("q", "> ", replace_first_only=True)
        | image()
        | internal_link()
        | list_()
    )
    # TODO: Why is a second pass needed?
    bbcode_complex = code_block() | table()
    return bbcode_complex.transform_string(bbcode_markup.transform_string(wikitext))


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

    def handle_markdown_links(self, body, source_folder) -> tuple[list, list]:
        note_links = []
        resources = []
        for link in common.get_markdown_links(body):
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
