"""Provides the base class for all converters."""

from datetime import datetime
import logging
from pathlib import Path

import pypandoc

import common
import intermediate_format as imf


class BaseConverter:

    def __init__(self, app: str):
        self.logger = logging.getLogger("jimmy")
        self.app = "Joplin Custom Importer" if app is None else app
        self.root_notebook: imf.Notebook
        self.root_path: Path | None = None

    def prepare_input(self, input_: Path) -> Path | None:
        """Prepare the input for further processing. For example extract an archive."""
        return input_

    def convert_multiple(self, files_or_folders: list[Path]) -> list[imf.Notebook]:
        """This is the main conversion function, called from the main app."""
        notebooks = []
        for input_index, file_or_folder in enumerate(files_or_folders):
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            index_suffix = "" if len(files_or_folders) == 1 else f" ({input_index})"
            self.root_notebook = imf.Notebook(
                {"title": f"{now} - Import from {self.app}{index_suffix}"}
            )
            self.convert(file_or_folder)
            notebooks.append(self.root_notebook)
        return notebooks

    def convert(self, file_or_folder: Path):
        pass


class DefaultConverter(BaseConverter):

    def convert_file(self, file_: Path, parent: imf.Notebook):
        """Default conversion function for files. Uses pandoc directly."""
        if file_.suffix.lower() in (".md", ".markdown", ".txt", ".text"):
            note_body = file_.read_text()
        else:
            # markdown output formats:
            # https://pandoc.org/chunkedhtml-demo/8.22-markdown-variants.html
            # Joplin follows CommonMark: https://joplinapp.org/help/apps/markdown
            note_body = pypandoc.convert_file(file_, "commonmark_x")
        parent.child_notes.append(
            imf.Note(
                {
                    "title": file_.stem,
                    "body": note_body,
                    **common.get_ctime_mtime_ms(file_),
                    "source_application": "jimmy",
                }
            )
        )

    def convert_folder(self, folder: Path, parent: imf.Notebook):
        """Default conversion function for folders."""
        for item in folder.iterdir():
            if item.is_file():
                try:
                    self.convert_file(item, parent)
                    self.logger.debug(f"ok   {item.name}")
                except Exception as exc:  # pylint: disable=broad-except
                    self.logger.debug(f"fail {item.name}: {str(exc).strip()[:120]}")
            else:
                new_parent = imf.Notebook(
                    {"title": item.stem, **common.get_ctime_mtime_ms(item)}
                )
                self.convert_folder(item, new_parent)
                parent.child_notebooks.append(new_parent)

    def convert(self, file_or_folder: Path):
        """This is the main conversion function, called from the main app."""
        conversion_function = (
            self.convert_file if file_or_folder.is_file() else self.convert_folder
        )
        conversion_function(file_or_folder, self.root_notebook)
