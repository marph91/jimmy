"""Convert notion notes to the intermediate format."""

import io
from pathlib import Path
from urllib.parse import unquote
import zipfile

import common
import converter
import intermediate_format as imf


class Converter(converter.BaseConverter):
    accepted_extensions = [".zip"]

    def prepare_input(self, input_: Path) -> Path:
        temp_folder = common.get_temp_folder()

        # unzip nested zip file in notion format
        with zipfile.ZipFile(input_) as zip_ref:
            for nested_zip_name in zip_ref.namelist():
                with zip_ref.open(nested_zip_name) as nested_zip:
                    nested_zip_filedata = io.BytesIO(nested_zip.read())
                    with zipfile.ZipFile(nested_zip_filedata) as nested_zip_ref:
                        nested_zip_ref.extractall(temp_folder)

        # Flatten folder structure. I. e. move all files to root directory.
        # https://stackoverflow.com/a/50368037/7410886
        for item in temp_folder.iterdir():
            if item.is_dir():
                for file_ in item.iterdir():
                    file_.rename(file_.parents[1] / file_.name)
                item.rmdir()
        return temp_folder

    def convert(self, file_or_folder: Path):
        self.root_path = self.prepare_input(file_or_folder)

        for item in self.root_path.iterdir():
            if item.is_dir() or item.suffix.lower() != ".md":
                continue
            # id is appended to filename
            title, original_id = item.stem.rsplit(" ", 1)
            # first line is title, second is whitespace
            body = "\n".join(item.read_text().split("\n")[2:])

            # find links
            resources = []
            note_links = []
            for link in common.get_markdown_links(body):
                if link.is_web_link or link.is_mail_link:
                    continue  # keep the original links
                if link.url.endswith(".md"):
                    # internal link
                    _, linked_note_id = Path(unquote(link.url)).stem.rsplit(" ", 1)
                    note_links.append(
                        imf.NoteLink(str(link), linked_note_id, link.text)
                    )
                elif (self.root_path / link.url).is_file():
                    # resource
                    resources.append(
                        imf.Resource(self.root_path / link.url, str(link), link.text)
                    )

            note_joplin = imf.Note(
                {
                    "title": title,
                    "body": body,
                    "source_application": self.format,
                },
                original_id=original_id,
                resources=resources,
                note_links=note_links,
            )
            self.root_notebook.child_notes.append(note_joplin)
