"""Convert textbundle or textpack notes to the intermediate format."""

from pathlib import Path
from urllib.parse import unquote

import converter
import intermediate_format as imf
import markdown_lib


class Converter(converter.BaseConverter):
    accepted_extensions = [".textbundle", ".textpack"]

    def handle_markdown_links(self, body: str) -> imf.Resources:
        resources = []
        for link in markdown_lib.common.get_markdown_links(body):
            if link.is_web_link or link.is_mail_link:
                continue  # keep the original links
            if link.text.startswith("^"):
                continue  # foot note (is working in Joplin without modification)
            # resource
            resource_path = self.root_path / unquote(link.url)
            if not resource_path.is_file():
                self.logger.warning(f"Couldn't find resource {resource_path}")
                continue
            resources.append(imf.Resource(resource_path, str(link), link.text))
        return resources

    def convert(self, file_or_folder: Path):
        # TODO: Are internal links and nested folders supported by this format?

        for file_ in sorted(self.root_path.iterdir()):
            if file_.suffix.lower() not in (".md", ".markdown"):
                # take only the exports in markdown format
                self.logger.debug(f"Ignoring folder or file {file_.name}")
                continue

            # Filename from textbundle name seems to be more robust
            # than taking the first line of the body.
            title = file_.parent.stem
            self.logger.debug(f'Converting note "{title}"')

            note_imf = imf.Note(
                title, file_.read_text(encoding="utf-8"), source_application=self.format
            )
            note_imf.tags = [
                imf.Tag(tag)
                for tag in markdown_lib.common.get_inline_tags(note_imf.body, ["#"])
            ]
            note_imf.resources = self.handle_markdown_links(note_imf.body)
            note_imf.time_from_file(file_)

            self.root_notebook.child_notes.append(note_imf)
