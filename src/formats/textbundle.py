"""Convert textbundle or textpack notes to the intermediate format."""

import itertools
from pathlib import Path
from urllib.parse import unquote

import common
import converter
import intermediate_format as imf
import markdown_lib


class Converter(converter.BaseConverter):
    accepted_extensions = [".textbundle", ".textpack"]
    accept_folder = True

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

    @common.catch_all_exceptions
    def convert_note(self, file_: Path, parent_notebook: imf.Notebook):
        if file_.suffix.lower() not in (".md", ".markdown"):
            # take only the exports in markdown format
            self.logger.debug(f'Ignoring folder or file "{file_.name}"')
            return

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

        parent_notebook.child_notes.append(note_imf)

    def convert(self, file_or_folder: Path):
        # TODO: Are internal links and nested folders supported by this format?

        # We can't check for "is_file()", since ".textbundle" is a folder.
        if file_or_folder.suffix in self.accepted_extensions:
            for file_ in sorted(self.root_path.iterdir()):
                self.convert_note(file_, self.root_notebook)
        else:
            for file_ in sorted(
                itertools.chain(
                    file_or_folder.glob("*.textbundle"),
                    file_or_folder.glob("*.textpack"),
                )
            ):
                self.root_path = self.prepare_input(file_)
                parent_notebook = imf.Notebook(file_.stem)
                self.root_notebook.child_notebooks.append(parent_notebook)
                for file_ in sorted(self.root_path.iterdir()):
                    self.convert_note(file_, parent_notebook)
