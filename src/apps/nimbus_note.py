from pathlib import Path
import zipfile

import pypandoc

from intermediate_format import Note


def convert(input_folder: Path, parent):
    for file_ in input_folder.glob("**/*.zip"):
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
                    note_joplin = Note(
                        {"title": file_.stem, "body": note_body_markdown.strip()}
                    )
                    parent.child_notes.append(note_joplin)
                    print(note_joplin)
    return parent, []
