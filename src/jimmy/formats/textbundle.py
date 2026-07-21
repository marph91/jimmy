"""Convert textbundle or textpack notes to the intermediate format."""

import itertools
import json
from pathlib import Path
from urllib.parse import unquote, urlparse

from jimmy import common, converter, intermediate_format as imf
import jimmy.md_lib.links
import jimmy.md_lib.tags
import jimmy.md_lib.text


class Converter(converter.BaseConverter):
    def handle_links(self, body: str) -> tuple[str, imf.Resources, imf.NoteLinks]:
        note_links = []
        resources = []
        for link in jimmy.md_lib.links.get_markdown_links(body):
            if link.is_web_link or link.is_mail_link or link.url.startswith("bear://"):
                continue  # keep the original links
            if link.text.startswith("^"):
                continue  # foot note (is working in Joplin without modification)

            # all wikilinks seem to be note links
            if link.is_wikilink:
                # strip sub-note links, like links to headings
                url = link.url.split("/", 1)[0].strip()
                note_links.append(imf.NoteLink(str(link), url, link.text or url))
            else:
                # resource
                resource_path = self.root_path / unquote(link.url)
                if resource_path.is_file():
                    resources.append(imf.Resource(resource_path, str(link), link.text))
                else:
                    if not urlparse(link.url).scheme:
                        body = body.replace(
                            jimmy.md_lib.links.make_link(
                                link.text, link.url, is_image=link.is_image
                            ),
                            jimmy.md_lib.links.make_link(
                                link.text, f"https://{link.url}", is_image=link.is_image
                            ),
                        )
        return body, resources, note_links

    @common.catch_all_exceptions
    def convert_note(self, file_: Path, parent_notebook: imf.Notebook, metadata: dict):
        if file_.name == "info.json":
            return  # handled already
        if file_.name == "assets":
            return  # not needed, since it's included in link paths
        if file_.suffix.lower() not in common.MARKDOWN_SUFFIXES:
            # take only the exports in markdown format
            self.logger.debug(f'Ignoring folder or file "{file_.name}"')
            return

        # Filename from textbundle name seems to be more robust
        # than taking the first line of the body.
        title = file_.parent.stem
        self.logger.debug(f'Converting note "{title}"')

        # title = first line header
        _, body = jimmy.md_lib.text.split_title_from_body(file_.read_text(encoding="utf-8"))
        body = body.replace(r"\#", "#")  # sometimes incorrectly escaped in bear
        # TODO: Convert Bear underline "~abc~" to Joplin underline "++abc++".
        note_imf = imf.Note(title, body, source_application=self.format)
        # TODO: Handle Bear multiword tags, like "#tag abc#".
        note_imf.tags = [
            imf.Tag(tag) for tag in jimmy.md_lib.tags.get_inline_tags(note_imf.body, ["#"])
        ]
        note_imf.body, note_imf.resources, note_imf.note_links = self.handle_links(note_imf.body)

        # handle bear specific metadata
        if (bear_metadata := metadata.get("net.shinyfrog.bear")) is not None:
            if (created := bear_metadata.get("creationDate")) is not None:
                note_imf.created = common.iso_to_datetime(created)
            if (updated := bear_metadata.get("modificationDate")) is not None:
                note_imf.updated = common.iso_to_datetime(updated)
            # ID renamed in v2?
            # There are IDs, but at the end, the title is used in wikilinks.
            # note_imf.original_id = bear_metadata.get(
            #     "uniqueIdentifier"
            # ) or bear_metadata.get("bear-note-unique-identifier")
            note_imf.original_id = title

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
            metadata = json.loads((self.root_path / "info.json").read_text(encoding="utf-8"))
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

                metadata = json.loads((self.root_path / "info.json").read_text(encoding="utf-8"))
                for file_ in sorted(self.root_path.iterdir()):
                    self.convert_note(file_, parent_notebook, metadata)
