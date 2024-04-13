"""Convert nimbus notes to the intermediate format."""

from pathlib import Path
import zipfile

import pypandoc

import converter
import intermediate_format as imf


class Converter(converter.BaseConverter):
    def convert(self, file_or_folder: Path):
        for file_ in file_or_folder.glob("**/*.zip"):
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
                    # Don't use "commonmark_x". There would be too many noise.
                    note_body_markdown = pypandoc.convert_text(
                        note_body_html, "markdown_strict-raw_html", format="html"
                    )
                    note_joplin = imf.Note(
                        {
                            "title": file_.stem,
                            "body": note_body_markdown.strip(),
                            "source_application": self.app,
                        }
                    )
                    self.root_notebook.child_notes.append(note_joplin)
