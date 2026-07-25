from pathlib import Path
import unittest

from jimmy import common, intermediate_format as imf
from jimmy.writer import PathDeterminer


class DetermineNotePaths(unittest.TestCase):
    def determine(self, title: str, max_name_length: int) -> Path:
        config = common.Config(max_name_length=max_name_length)
        notebook = imf.Notebook("root", child_notes=[imf.Note(title)])
        notebook.path = Path("notebook")
        PathDeterminer(config).determine_paths(notebook)
        path = notebook.child_notes[0].path
        assert path is not None
        return path

    def test_long_title_respects_max_name_length(self):
        # The ".md" suffix is appended after truncation, so it has to be
        # accounted for. Otherwise writing the note fails with
        # "OSError: [Errno 36] File name too long".
        path = self.determine("a" * 400, 255)
        self.assertEqual(len(path.name), 255)
        self.assertEqual(path.suffix, ".md")

    def test_short_title_is_unchanged(self):
        path = self.determine("note", 255)
        self.assertEqual(path.name, "note.md")
