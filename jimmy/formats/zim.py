"""Convert Zim Wiki notes to the intermediate format."""

from pathlib import Path

from jimmy import common, converter, intermediate_format as imf
import jimmy.md_lib.common
from jimmy.md_lib.zim import zim_to_md


class Converter(converter.BaseConverter):
    accept_folder = True

    def handle_markdown_links(self, body: str) -> tuple[imf.Resources, imf.NoteLinks]:
        # https://zim-wiki.org/manual/Help/Links.html
        note_links = []
        resources = []
        for link in jimmy.md_lib.common.get_markdown_links(body):
            if link.is_web_link or link.is_mail_link:
                continue  # keep the original links
            if link.url.startswith("#"):
                # Links that start with a '#' are resolved as links within
                # the page to a heading or an object
                continue
            if link.url.startswith("file://"):
                continue  # external file, keep it as-is
            if "/" in link.url:
                # internal file
                resources.append(imf.Resource(Path(link.url), str(link), link.text))
            else:
                # internal link
                linked_note_id = Path(link.url.split(":")[-1]).stem
                note_links.append(imf.NoteLink(str(link), linked_note_id, link.text))
        return resources, note_links

    @common.catch_all_exceptions
    def convert_note(self, item: Path, parent: imf.Notebook):
        if item.name == "notebook.zim" or item.suffix.lower() != ".txt":
            return

        # note
        title = item.stem.replace("_", " ")  # underscores seem to be replaced
        self.logger.debug(f'Converting note "{title}"')

        imf_note = imf.Note(title, source_application=self.format, original_id=title)

        item_content = item.read_text(encoding="utf-8")
        try:
            metadata, _, body = item_content.split("\n\n", maxsplit=2)
        except ValueError:
            body = item_content
            metadata = ""

        for line in metadata.split("\n"):
            try:
                key, value = line.split(": ", maxsplit=1)
            except ValueError:
                self.logger.debug("Failed to parse metadata. Probably only a txt attachment.")
                return

            match key:
                case "Content-Type":
                    if value != "text/x-zim-wiki":
                        self.logger.warning(
                            f'Unexpected content type "{value}". Trying to parse anyway.'
                        )
                case "Creation-Date":
                    imf_note.created = common.iso_to_datetime(value)

        resource_path = item.parent / item.stem
        imf_note.body = zim_to_md(body, resource_path)

        resources, note_links = self.handle_markdown_links(imf_note.body)
        imf_note.resources = resources
        imf_note.note_links = note_links

        # tags: https://zim-wiki.org/manual/Help/Tags.html
        # TODO: exclude invalid characters
        imf_note.tags = [imf.Tag(tag) for tag in jimmy.md_lib.common.get_inline_tags(body, ["@"])]

        parent.child_notes.append(imf_note)

    def convert_folder(self, folder: Path, parent: imf.Notebook):
        for item in sorted(folder.iterdir()):
            if item.is_dir():
                # notebook
                new_parent = imf.Notebook(item.name)
                self.convert_folder(item, new_parent)
                parent.child_notebooks.append(new_parent)
                continue
            self.convert_note(item, parent)

    def convert(self, file_or_folder: Path):
        self.root_path = file_or_folder
        self.convert_folder(file_or_folder, self.root_notebook)
        # Don't export empty notebooks
        self.remove_empty_notebooks()
