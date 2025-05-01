"""Convert textbundle or textpack notes to the intermediate format."""

import itertools
import json
from pathlib import Path
from urllib.parse import unquote

from jimmy import common, converter, intermediate_format as imf
import jimmy.md_lib.common


class Converter(converter.BaseConverter):
    accepted_extensions = [".textbundle", ".textpack"]
    accept_folder = True

    def handle_markdown_links(self, body: str) -> imf.Resources:
        resources = []
        for link in jimmy.md_lib.common.get_markdown_links(body):
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
    def convert_note(self, file_: Path, parent_notebook: imf.Notebook, metadata: dict):
        if file_.name == "info.json":
            return  # handled already
        if file_.name == "assets":
            return  # not needed, since it's included in link paths
        if file_.suffix.lower() not in (".md", ".markdown"):
            # take only the exports in markdown format
            self.logger.debug(f'Ignoring folder or file "{file_.name}"')
            return

        # Filename from textbundle name seems to be more robust
        # than taking the first line of the body.
        title = file_.parent.stem
        self.logger.debug(f'Converting note "{title}"')

        # title = first line header
        _, body = jimmy.md_lib.common.split_title_from_body(
            file_.read_text(encoding="utf-8")
        )
        note_imf = imf.Note(title, body, source_application=self.format)
        note_imf.tags = [
            imf.Tag(tag)
            for tag in jimmy.md_lib.common.get_inline_tags(note_imf.body, ["#"])
        ]
        note_imf.resources = self.handle_markdown_links(note_imf.body)

        # handle bear specific metadata
        if (bear_metadata := metadata.get("net.shinyfrog.bear")) is not None:
            note_imf.created = bear_metadata.get("creationDate")
            note_imf.updated = bear_metadata.get("modificationDate")
            # ID renamed in v2?
            note_imf.original_id = bear_metadata.get(
                "uniqueIdentifier"
            ) or bear_metadata.get("bear-note-unique-identifier")

            for key in ("pinned", "trashed", "archived"):
                if bool(int(bear_metadata.get(key, False))):
                    note_imf.tags.append(imf.Tag(f"bear-{key}"))

        if note_imf.created is None and note_imf.updated is None:
            note_imf.time_from_file(file_)

        parent_notebook.child_notes.append(note_imf)

    def convert(self, file_or_folder: Path):
        # TODO: Are internal links and nested folders supported by this format?

        # We can't check for "is_file()", since ".textbundle" is a folder.
        if file_or_folder.suffix in self.accepted_extensions:
            metadata = json.loads(
                (self.root_path / "info.json").read_text(encoding="utf-8")
            )
            for file_ in sorted(self.root_path.iterdir()):
                self.convert_note(file_, self.root_notebook, metadata)
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

                metadata = json.loads(
                    (self.root_path / "info.json").read_text(encoding="utf-8")
                )
                for file_ in sorted(self.root_path.iterdir()):
                    self.convert_note(file_, parent_notebook, metadata)
