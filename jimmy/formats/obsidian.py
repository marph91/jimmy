"""Convert obsidian notes to the intermediate format."""

from pathlib import Path
from urllib.parse import unquote

import frontmatter

from jimmy import common, converter, intermediate_format as imf
import jimmy.md_lib.common


class Converter(converter.BaseConverter):
    accept_folder = True

    def handle_markdown_links(self, body: str) -> tuple[imf.Resources, imf.NoteLinks]:
        note_links = []
        resources = []
        for link in jimmy.md_lib.common.get_markdown_links(body):
            if link.is_web_link or link.is_mail_link:
                continue  # keep the original links
            if any(
                link.url.endswith(md_suffix) for md_suffix in common.MARKDOWN_SUFFIXES
            ):
                # internal link
                linked_note_id = Path(unquote(link.url)).stem
                note_links.append(imf.NoteLink(str(link), linked_note_id, link.text))
            else:
                # resource
                resource_path = common.find_file_recursively(self.root_path, link.url)
                if resource_path is None:
                    continue
                resources.append(imf.Resource(resource_path, str(link), link.text))
        return resources, note_links

    def handle_wikilink_links(self, body: str) -> tuple[imf.Resources, imf.NoteLinks]:
        # https://help.obsidian.md/Linking+notes+and+files/Internal+links
        note_links = []
        resources = []
        for file_prefix, url, description in jimmy.md_lib.common.get_wikilink_links(
            body
        ):
            alias = "" if description.strip() == "" else f"|{description}"
            original_text = f"{file_prefix}[[{url}{alias}]]"
            if file_prefix:
                # resource
                resource_path = common.find_file_recursively(self.root_path, url)
                if resource_path is None:
                    continue
                resources.append(
                    imf.Resource(resource_path, original_text, description or url)
                )
            else:
                # internal link
                note_links.append(imf.NoteLink(original_text, url, description or url))
        return resources, note_links

    def handle_links(self, body: str) -> tuple[imf.Resources, imf.NoteLinks]:
        # Resources can be anywhere:
        # https://help.obsidian.md/Editing+and+formatting/Attachments#Change+default+attachment+location
        wikilink_resources, wikilink_note_links = self.handle_wikilink_links(body)
        markdown_resources, markdown_note_links = self.handle_markdown_links(body)
        return (
            wikilink_resources + markdown_resources,
            wikilink_note_links + markdown_note_links,
        )

    @common.catch_all_exceptions
    def convert_note(self, item: Path, parent: imf.Notebook):
        if item.suffix.lower() not in common.MARKDOWN_SUFFIXES:
            return
        title = item.stem
        self.logger.debug(f'Converting note "{title}"')

        body = item.read_text(encoding="utf-8")
        resources, note_links = self.handle_links(body)

        # https://help.obsidian.md/Editing+and+formatting/Tags
        inline_tags = jimmy.md_lib.common.get_inline_tags(body, ["#"])

        # frontmatter tags
        # https://help.obsidian.md/Editing+and+formatting/Properties#Default+properties
        metadata, body = frontmatter.parse(body)
        frontmatter_tags = metadata.get("tags", [])

        # aliases seem to be only used in the link description
        # frontmatter_.get("aliases", [])

        parent.child_notes.append(
            imf.Note(
                title,
                body,
                source_application=self.format,
                tags=[imf.Tag(tag) for tag in inline_tags + frontmatter_tags],
                resources=resources,
                note_links=note_links,
            )
        )

    def convert_folder(self, folder: Path, parent: imf.Notebook):
        for item in sorted(folder.iterdir()):
            if item.is_dir() and item.name == ".obsidian":
                continue  # ignore the internal obsidian folder
            if item.is_file():
                self.convert_note(item, parent)
            else:
                new_parent = imf.Notebook(item.name)
                self.convert_folder(item, new_parent)
                parent.child_notebooks.append(new_parent)

    def convert(self, file_or_folder: Path):
        self.convert_folder(file_or_folder, self.root_notebook)
