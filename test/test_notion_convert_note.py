import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest

import jimmy.main  # noqa: F401  (populates the format registry)

from jimmy.formats.notion import Converter
from jimmy import intermediate_format as imf


class TestNotionConvertNote(unittest.TestCase):
    def convert_file(self, tmp_path: Path, filename: str, body: str = "content"):
        config = SimpleNamespace(
            format="notion",
            password=None,
            frontmatter=None,
            template_file=None,
            output_folder=tmp_path,
        )
        converter = Converter(config)
        parent_notebook = imf.Notebook(title="root", original_id=".")
        note_file = tmp_path / filename
        note_file.write_text(body, encoding="utf-8")
        converter.convert_note(note_file, tmp_path, parent_notebook)
        return converter, parent_notebook

    def test_filename_without_space(self):
        # Notion titles can be empty, which yields a filename without the
        # " <id>" separator. Used to crash with "not enough values to unpack".
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            converter, parent_notebook = self.convert_file(tmp_path, "448ef1b0.md")

            self.assertIn("448ef1b0", converter.id_path_map)
            self.assertEqual(len(parent_notebook.child_notes), 1)
            self.assertEqual(parent_notebook.child_notes[0].title, "448ef1b0")
            self.assertEqual(parent_notebook.child_notes[0].original_id, "448ef1b0")

    def test_filename_with_space(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            converter, parent_notebook = self.convert_file(
                tmp_path, "My Note 1234abcd.md", body="Some content"
            )

            self.assertIn("1234abcd", converter.id_path_map)
            self.assertEqual(len(parent_notebook.child_notes), 1)
            self.assertEqual(parent_notebook.child_notes[0].title, "My Note")
            self.assertEqual(parent_notebook.child_notes[0].original_id, "1234abcd")


if __name__ == "__main__":
    unittest.main()
