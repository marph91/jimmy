"""Convert clipto notes to the intermediate format."""

from pathlib import Path
import zipfile

import common
import converter
import intermediate_format as imf


def handle_markdown_links(body: str, root_folder: Path) -> tuple[list, list]:
    note_links = []
    for file_prefix, description, url in common.get_markdown_links(body):
        original_text = f"{file_prefix}[{description}]({url})"
        if url.startswith("https://dynalist.io/d"):
            # Most likely internal link. We can only try to match against the name
            # (that might me modified in the meantime).
            if (
                common.find_file_recursively(root_folder, f"{description}.txt")
                is not None
            ):
                note_links.append(imf.NoteLink(original_text, description, description))
        elif url.startswith("http"):
            continue  # web link
        else:
            # TODO: There are no resources in dynalist free plan.
            pass
    return [], note_links


class Converter(converter.BaseConverter):

    def prepare_input(self, input_: Path) -> Path | None:
        """Prepare the input for further processing. For example extract an archive."""
        if input_.suffix.lower() == ".zip":
            temp_folder = common.get_temp_folder()
            with zipfile.ZipFile(input_) as zip_ref:
                zip_ref.extractall(temp_folder)
            return temp_folder
        if input_.is_dir():
            return input_
        self.logger.error("Unsupported format for dynalist")
        return None

    def convert(self, file_or_folder: Path):
        """This is the main conversion function, called from the main app."""
        self.root_path = self.prepare_input(file_or_folder)
        if self.root_path is None:
            return
        self.convert_folder(self.root_path, self.root_notebook)

    def convert_folder(self, folder: Path, parent: imf.Notebook):
        for item in folder.iterdir():
            if item.is_file():
                # We get a zip with opml and txt. Only advantage of opml over txt is
                # the owner attribute. So just use txt, because it's simpler.
                # opml is supported by pandoc, but the import is not working properly.
                if item.suffix != ".txt":
                    continue
                body = item.read_text()

                resources, note_links = handle_markdown_links(body, self.root_path)
                tags = common.get_inline_tags(body, ["#", "@"])

                parent.child_notes.append(
                    imf.Note(
                        {
                            "title": item.stem,
                            "body": body,
                            "source_application": self.app,
                        },
                        tags=[imf.Tag({"title": tag}, tag) for tag in tags],
                        resources=resources,
                        note_links=note_links,
                        original_id=item.stem,
                    )
                )
            else:
                new_parent = imf.Notebook(
                    {"title": item.name, **common.get_ctime_mtime_ms(item)}
                )
                self.convert_folder(item, new_parent)
                parent.child_notebooks.append(new_parent)
