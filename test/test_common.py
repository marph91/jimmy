"""Regression tests for jimmy.common helpers."""

import unittest
from pathlib import Path

import jimmy.common


class TestCommon(unittest.TestCase):
    def test_guess_suffix_missing_file(self):
        self.assertEqual(jimmy.common.guess_suffix(Path("non/existing.txt")), "")

    def test_is_image_missing_file(self):
        self.assertFalse(jimmy.common.is_image(Path("non/existing.txt")))


if __name__ == "__main__":
    unittest.main()
