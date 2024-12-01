"""Convert Zim Wiki notes to the intermediate format."""

import datetime as dt
from pathlib import Path
import re

import converter
import intermediate_format as imf
import markdown_lib.common
from markdown_lib.zim import zim_to_md


ZIM_IMAGE_REGEX = re.compile(r"(\{\{(.*?)\}\})")


class Converter(converter.BaseConverter):
    accept_folder = True

    @staticmethod
    def resolve_resource(resource_path: Path, url: Path) -> Path:
        # relative resources are stored in a folder named like the note
        # example:
        # - note.md
        # - note/image.png
        return url if Path(url).is_absolute() else resource_path / url

    def handle_zim_links(
        self, body: str, resource_path: Path
    ) -> tuple[imf.Resources, imf.NoteLinks]:
        # https://zim-wiki.org/manual/Help/Links.html
        # https://zim-wiki.org/manual/Help/Wiki_Syntax.html
        note_links = []
        resources = []
        for _, url, description in markdown_lib.common.get_wikilink_links(body):
            original_text = f"[[{url}]]"
            if "/" in url:
                # resource
                # Links containing a '/' are considered links to external files
                resources.append(
                    imf.Resource(
                        self.resolve_resource(resource_path, url),
                        original_text,
                        description or url,
                    )
                )
            elif "?" in url:
                # Links that contain a '?' are interwiki links
                pass  # interwiki links can't be resolved
            elif url.startswith("#"):
                # Links that start with a '#' are resolved as links
                # within the page to a heading or an object
                pass  # they don't need to be resolved
            else:
                # Ignore other directives for now.
                # TODO: Find a way to map them. Right now we only map by
                # matching the original_id.
                original_id = url.split(":")[-1].lstrip("+")
                note_links.append(
                    imf.NoteLink(original_text, original_id, description or original_id)
                )
        return resources, note_links

    def handle_zim_images(self, body: str, resource_path: Path) -> imf.Resources:
        images = []
        for original_text, image_link in ZIM_IMAGE_REGEX.findall(body):
            image_link = Path(image_link)
            images.append(
                imf.Resource(
                    self.resolve_resource(resource_path, image_link),
                    original_text,
                    image_link.name,
                )
            )
        return images

    def convert_folder(self, folder: Path, parent: imf.Notebook):
        # pylint: disable=too-many-locals
        for item in sorted(folder.iterdir()):
            if item.is_dir():
                # notebook
                new_parent = imf.Notebook(item.name)
                self.convert_folder(item, new_parent)
                parent.child_notebooks.append(new_parent)
                continue
            if item.name == "notebook.zim" or item.suffix.lower() != ".txt":
                continue

            # note
            title = item.stem.replace("_", " ")  # underscores seem to be replaced
            self.logger.debug(f'Converting note "{title}"')

            imf_note = imf.Note(
                title, source_application=self.format, original_id=title
            )

            item_content = item.read_text(encoding="utf-8")
            try:
                metadata, _, body = item_content.split("\n\n", maxsplit=2)
            except ValueError:
                body = item_content
                metadata = ""

            for line in metadata.split("\n"):
                key, value = line.split(": ", maxsplit=1)
                if key == "Creation-Date":
                    imf_note.created = dt.datetime.fromisoformat(value)

            imf_note.body = zim_to_md(body)

            resource_path = folder / item.stem
            resources, note_links = self.handle_zim_links(imf_note.body, resource_path)
            imf_note.resources = resources
            imf_note.note_links = note_links

            imf_note.resources.extend(
                self.handle_zim_images(imf_note.body, resource_path)
            )

            # tags: https://zim-wiki.org/manual/Help/Tags.html
            # TODO: exclude invalid characters
            imf_note.tags = [
                imf.Tag(tag) for tag in markdown_lib.common.get_inline_tags(body, ["@"])
            ]

            parent.child_notes.append(imf_note)

    def convert(self, file_or_folder: Path):
        self.root_path = file_or_folder
        self.convert_folder(file_or_folder, self.root_notebook)
