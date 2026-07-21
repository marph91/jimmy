import unittest

import bs4

import jimmy.md_lib.html_filter as filter


class MergeConsecutiveFormatting(unittest.TestCase):
    def test_duplicate_parent(self):
        soup = bs4.BeautifulSoup("<b><b>bold</b></b>", "html.parser")
        filter.merge_consecutive_formatting(soup)
        assert str(soup) == "<b>bold</b>"

    def test_consecutive_sibling(self):
        soup = bs4.BeautifulSoup("<b>bold1 </b><b>bold2</b>", "html.parser")
        filter.merge_consecutive_formatting(soup)
        assert str(soup) == "<b>bold1 bold2</b>"

    def test_consecutive_parent_sibling(self):
        soup = bs4.BeautifulSoup("<u>first tag </u><span><u>second tag</u></span>", "html.parser")
        filter.merge_consecutive_formatting(soup)
        assert str(soup) == "<u>first tag <span>second tag</span></u>"

    def test_consecutive_parent_siblings(self):
        soup = bs4.BeautifulSoup(
            "<div>• <strong>abc</strong><span><strong>d</strong></span><strong>efg</strong></div>",
            "html.parser",
        )
        filter.merge_consecutive_formatting(soup)
        assert str(soup) == "<div>• <strong>abc<span>d</span>efg</strong></div>"
