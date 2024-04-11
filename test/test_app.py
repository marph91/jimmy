import sys
from pathlib import Path

# ensure that we can access the code
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import unittest

import joplin_custom_importer as jci


TEST_INPUTS = Path("test_inputs")


class Base(unittest.TestCase):

    def assert_stats(
        self, actual_stats, notebooks=1, notes=0, resources=0, tags=0, note_links=0
    ):
        expected_stats = {
            "notebooks": notebooks,
            "notes": notes,
            "resources": resources,
            "tags": tags,
            "note_links": note_links,
        }
        self.assertDictEqual(actual_stats, expected_stats)

    def get_stats(self, inputs, app):
        note_tree = jci.convert_all_inputs(inputs, app)
        return jci.get_import_stats(note_tree)


class Apps(Base):

    def test_clipto(self):
        stats = self.get_stats(
            [TEST_INPUTS / "clipto/clipto_backup_240401_105154.json"], "clipto"
        )
        self.assert_stats(stats, notes=3, tags=1)

    def test_google_keep(self):
        stats = self.get_stats([TEST_INPUTS / "Google Keep"], "google_keep")
        self.assert_stats(stats, notes=3, resources=1, tags=3)

    def test_nimbus_note(self):
        # TODO
        self.skipTest("no public test data yet")

    def test_notion(self):
        # TODO
        self.skipTest("no public test data yet")

    def test_obsidian(self):
        stats = self.get_stats([TEST_INPUTS / "obsidian_vault"], "obsidian")
        self.assert_stats(stats, notebooks=2, notes=2, resources=2, note_links=2)

    def test_simplenote(self):
        stats = self.get_stats([TEST_INPUTS / "simplenote"], "simplenote")
        self.assert_stats(stats, notes=2, tags=2, note_links=1)

    def test_tiddlywiki(self):
        # TODO
        self.skipTest("no public test data yet")

    def test_todo_txt(self):
        # contexts and projects are converted to tags
        stats = self.get_stats(
            [TEST_INPUTS / "todo_txt/examples_from_readme.txt"], "todo_txt"
        )
        self.assert_stats(stats, notes=32, tags=47)

    def test_todoist(self):
        # priorities are converted to tags
        stats = self.get_stats([TEST_INPUTS / "todoist/Privates.csv"], "todoist")
        self.assert_stats(stats, notebooks=6, notes=21, tags=25)


class Arbitrary(Base):
    arbitrary_folder = TEST_INPUTS / "arbitrary_folder"

    def test_single_folder(self):
        # .adoc is not converted (yet)
        stats = self.get_stats([self.arbitrary_folder], None)
        self.assert_stats(stats, notebooks=2, notes=4)

    def test_multiple_folders(self):
        stats = self.get_stats([self.arbitrary_folder] * 2, None)
        self.assert_stats(stats, notebooks=3, notes=8)

    def test_single_file(self):
        stats = self.get_stats([self.arbitrary_folder / "plaintext.txt"], None)
        self.assert_stats(stats, notes=1)

    def test_multiple_files(self):
        stats = self.get_stats([self.arbitrary_folder / "plaintext.txt"] * 2, None)
        self.assert_stats(stats, notes=2)

    def test_markdown(self):
        stats = self.get_stats([self.arbitrary_folder / "sample.md"], None)
        self.assert_stats(stats, notes=1)
