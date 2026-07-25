from pathlib import Path
import tempfile
import unittest

from jimmy import common, intermediate_format as imf
import jimmy.formats.obsidian


class FrontmatterTags(unittest.TestCase):
    def convert_note(self, body: str) -> imf.Note:
        converter = jimmy.formats.obsidian.Converter(common.Config(format="obsidian"))
        parent = imf.Notebook("root")
        with tempfile.TemporaryDirectory() as folder:
            converter.root_path = Path(folder)
            note_path = Path(folder) / "note.md"
            note_path.write_text(body, encoding="utf-8")
            converter.convert_note(note_path, parent)
        return parent.child_notes[0]

    def test_bare_hash_tag_is_dropped(self):
        # A bare "#" starts a YAML comment, so the tag list entry parses as None.
        note = self.convert_note("---\ntags:\n  - Self Discovery\n  - #\n---\n\nbody\n")
        assert [tag.title for tag in note.tags] == ["Self Discovery"]
        note.apply_frontmatter("joplin")
        assert "self discovery" in note.body
