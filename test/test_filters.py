import copy
from types import SimpleNamespace
import unittest

from jimmy import common
from jimmy.filters import apply_filters
from jimmy import intermediate_format as imf


TEST_NOTE_TREE = [
    imf.Notebook(
        "Default root folder - imported always",
        child_notebooks=[
            imf.Notebook(
                "Nested notebook 1",
                child_notes=[
                    imf.Note(
                        "Nested note 1",
                        tags=[imf.Tag("test tag 1"), imf.Tag("test tag 2")],
                    ),
                    imf.Note("Nested note 2"),
                ],
            ),
            imf.Notebook(
                "Nested notebook 2",
                child_notebooks=[imf.Notebook("Nested notebook - level 2")],
                child_notes=[imf.Note("Nested note 3")],
            ),
        ],
        child_notes=[imf.Note("root note 1", tags=[imf.Tag("test tag 1")])],
    )
]


class Base(unittest.TestCase):
    def setUp(self):
        self.test_tree = copy.deepcopy(TEST_NOTE_TREE)

        # mock a argparse namespace
        # https://stackoverflow.com/a/51197422/7410886
        self.config = SimpleNamespace(
            exclude_notes=None,
            include_notes=None,
            exclude_notes_with_tags=None,
            include_notes_with_tags=None,
            exclude_tags=None,
            include_tags=None,
        )

    def assert_tree_stats(self, expected_stats):
        actual_stats = common.get_import_stats(self.test_tree)
        self.assertEqual(actual_stats, expected_stats)


class Notes(Base):
    def test_exclude_single(self):
        self.config.exclude_notes = ["Nested note 2"]
        apply_filters(self.test_tree, self.config)
        self.assert_tree_stats(common.Stats(notebooks=4, notes=3, tags=3))

    def test_exclude_multiple(self):
        self.config.exclude_notes = ["Nested note 2", "root note 1"]
        apply_filters(self.test_tree, self.config)
        self.assert_tree_stats(common.Stats(notebooks=4, notes=2, tags=2))

    def test_include_single(self):
        self.config.include_notes = ["Nested note 2"]
        apply_filters(self.test_tree, self.config)
        self.assert_tree_stats(common.Stats(notebooks=4, notes=1))

    def test_include_multiple(self):
        self.config.include_notes = ["Nested note 2", "root note 1"]
        apply_filters(self.test_tree, self.config)
        self.assert_tree_stats(common.Stats(notebooks=4, notes=2, tags=1))

    def test_exclude_single_by_tag(self):
        self.config.exclude_notes_with_tags = ["test tag 2"]
        apply_filters(self.test_tree, self.config)
        self.assert_tree_stats(common.Stats(notebooks=4, notes=3, tags=1))

    def test_exclude_multiple_by_tag(self):
        self.config.exclude_notes_with_tags = ["test tag 2", "test tag 1"]
        apply_filters(self.test_tree, self.config)
        self.assert_tree_stats(common.Stats(notebooks=4, notes=2))

    def test_exclude_all_by_tag_wildcard(self):
        self.config.exclude_notes_with_tags = ["*"]
        apply_filters(self.test_tree, self.config)
        self.assert_tree_stats(common.Stats(notebooks=4, notes=2))

    def test_include_single_by_tag(self):
        self.config.include_notes_with_tags = ["test tag 2"]
        apply_filters(self.test_tree, self.config)
        self.assert_tree_stats(common.Stats(notebooks=4, notes=1, tags=2))

    def test_include_multiple_by_tag(self):
        self.config.include_notes_with_tags = ["test tag 1", "test tag 2"]
        apply_filters(self.test_tree, self.config)
        self.assert_tree_stats(common.Stats(notebooks=4, notes=2, tags=3))

    def test_include_all_by_tag_wildcard(self):
        self.config.include_notes_with_tags = ["*"]
        apply_filters(self.test_tree, self.config)
        self.assert_tree_stats(common.Stats(notebooks=4, notes=2, tags=3))


class Tags(Base):
    def test_exclude_single(self):
        self.config.exclude_tags = ["test tag 1"]
        apply_filters(self.test_tree, self.config)
        self.assert_tree_stats(common.Stats(notebooks=4, notes=4, tags=1))

    def test_exclude_multiple(self):
        self.config.exclude_tags = ["test tag 1", "test tag 2"]
        apply_filters(self.test_tree, self.config)
        self.assert_tree_stats(common.Stats(notebooks=4, notes=4, tags=0))

    def test_exclude_all_wildcard(self):
        self.config.exclude_tags = ["*"]
        apply_filters(self.test_tree, self.config)
        self.assert_tree_stats(common.Stats(notebooks=4, notes=4, tags=0))

    def test_include_single(self):
        self.config.include_tags = ["test tag 1"]
        apply_filters(self.test_tree, self.config)
        self.assert_tree_stats(common.Stats(notebooks=4, notes=4, tags=2))

    def test_include_multiple(self):
        self.config.include_tags = ["test tag 1", "test tag 2"]
        apply_filters(self.test_tree, self.config)
        self.assert_tree_stats(common.Stats(notebooks=4, notes=4, tags=3))

    def test_include_all_wildcard(self):
        self.config.include_tags = ["test tag *"]
        apply_filters(self.test_tree, self.config)
        self.assert_tree_stats(common.Stats(notebooks=4, notes=4, tags=3))

        self.config.include_tags = ["*"]
        apply_filters(self.test_tree, self.config)
        self.assert_tree_stats(common.Stats(notebooks=4, notes=4, tags=3))
