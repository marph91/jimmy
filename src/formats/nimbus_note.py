"""Convert nimbus notes to the intermediate format."""

from pathlib import Path
import zipfile

import common
import converter
import intermediate_format as imf


class Converter(converter.BaseConverter):
    accept_folder = True

    def convert(self, file_or_folder: Path):
        for file_ in file_or_folder.rglob("*.zip"):
            title = file_.stem
            self.logger.debug(f'Converting note "{title}"')
            with zipfile.ZipFile(file_) as zip_ref:
                # HTML note seems to have the name "note.html" always
                html_notes = [
                    zipped_file
                    for zipped_file in zip_ref.namelist()
                    if zipped_file.endswith(".html")
                ]
                for html_note in html_notes:
                    with zip_ref.open(html_note) as zip_note:
                        note_body_html = zip_note.read().decode("UTF-8")
                    note_body_markdown = common.markup_to_markdown(note_body_html)
                    note_imf = imf.Note(
                        title,
                        note_body_markdown.strip(),
                        source_application=self.format,
                    )
                    self.root_notebook.child_notes.append(note_imf)
