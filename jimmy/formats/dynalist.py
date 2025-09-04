"""Convert clipto notes to the intermediate format."""

from pathlib import Path

from jimmy import common, converter, intermediate_format as imf
import jimmy.md_lib.common


def handle_markdown_links(body: str, root_folder: Path) -> imf.NoteLinks:
    note_links = []
    for link in jimmy.md_lib.common.get_markdown_links(body):
        if link.url.startswith("https://dynalist.io/d"):
            # Most likely internal link. We can only try to match against the name
            # (that might be modified in the meantime).
            if common.find_file_recursively(root_folder, f"{link.text}.txt") is not None:
                note_links.append(imf.NoteLink(str(link), link.text, link.text))
        elif link.is_web_link or link.is_mail_link:
            continue  # keep the original links
        else:
            # TODO: There are no resources in dynalist free plan.
            pass
    return note_links


class Converter(converter.BaseConverter):
    accepted_extensions = [".zip"]

    @common.catch_all_exceptions
    def convert_note(self, item: Path, parent: imf.Notebook):
        # We get a zip with opml and txt. Only advantage of opml over txt is
        # the owner attribute. So just use txt, because it's simpler.
        # opml is supported by pandoc, but the import is not working properly.
        if item.suffix.lower() != ".txt":
            return
        title = item.stem
        self.logger.debug(f'Converting note "{title}"')

        note_imf = imf.Note(
            title,
            item.read_text(encoding="utf-8"),
            source_application=self.format,
        )
        note_imf.tags = [
            imf.Tag(tag) for tag in jimmy.md_lib.common.get_inline_tags(note_imf.body, ["#", "@"])
        ]
        note_imf.note_links = handle_markdown_links(note_imf.body, self.root_path)
        parent.child_notes.append(note_imf)

    def convert_folder(self, folder: Path, parent: imf.Notebook):
        for item in sorted(folder.iterdir()):
            if item.is_file():
                self.convert_note(item, parent)
            else:
                new_parent = imf.Notebook(item.name)
                self.convert_folder(item, new_parent)
                parent.child_notebooks.append(new_parent)

    def convert(self, file_or_folder: Path):
        self.convert_folder(self.root_path, self.root_notebook)
