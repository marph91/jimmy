"""Convert a sqlite database to the intermediate format."""

from pathlib import Path
import sqlite3

import converter
import intermediate_format as imf
import markdown_lib


class Converter(converter.BaseConverter):
    accepted_extensions = [".db"]

    def convert(self, file_or_folder: Path):
        # https://stackoverflow.com/a/10746045/7410886
        conn = sqlite3.connect(file_or_folder)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master where type='table';")
        for table_name in cur.fetchall():
            table_name = table_name[0]

            self.logger.debug(f'Converting note "{table_name}"')

            # TODO: is ".header on" and ".mode markdown" possible?
            # https://markdown.land/sqlite-markdown#using-sqlites-markdown-mode
            cur.execute(f"SELECT * FROM {table_name}")
            table_md = markdown_lib.common.MarkdownTable(
                [[i[0] for i in cur.description]],
                [[str(cell) for cell in row] for row in cur.fetchall()],
            )

            note_imf = imf.Note(table_name, table_md.create_md())
            self.root_notebook.child_notes.append(note_imf)

        cur.close()
        conn.close()
