import copy
import unittest

from jimmy import intermediate_format as imf


TEST_NOTEBOOK = imf.Notebook(
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


class GetAllNotes(unittest.TestCase):
    def setUp(self):
        self.test_notebook = copy.deepcopy(TEST_NOTEBOOK)

    def test_no_child_notes(self):
        notes = imf.Notebook("test").get_all_child_notes()
        assert len(list(notes)) == 0

    def test_example_notebook(self):
        notes = self.test_notebook.get_all_child_notes()
        assert len(list(notes)) == 4

        notes = self.test_notebook.get_all_child_notes()
        assert next(notes).title == "root note 1"
        assert next(notes).title == "Nested note 1"
        assert next(notes).title == "Nested note 2"
        assert next(notes).title == "Nested note 3"


class GetAllNotebooks(unittest.TestCase):
    def setUp(self):
        self.test_notebook = copy.deepcopy(TEST_NOTEBOOK)

    def test_no_child_notes(self):
        notebooks = imf.Notebook("test").get_all_child_notebooks()
        assert len(list(notebooks)) == 0

    def test_example_notebook(self):
        notebooks = self.test_notebook.get_all_child_notebooks()
        assert len(list(notebooks)) == 3

        notebooks = self.test_notebook.get_all_child_notebooks()
        assert next(notebooks).title == "Nested notebook 1"
        assert next(notebooks).title == "Nested notebook 2"
        assert next(notebooks).title == "Nested notebook - level 2"
