import difflib
import filecmp
from pathlib import Path
from types import SimpleNamespace
import random
import shutil
import unittest

from parameterized import parameterized

import jimmy


def name_func(testcase_func, param_num, param):
    return f"{testcase_func.__name__}_{Path(param[0][0][0]).parent}"


class EndToEnd(unittest.TestCase):
    def setUp(self):
        jimmy.setup_logging(False, "DEBUG")

        # use the same seed before every test to get reproducible uuids
        random.seed(42)

        # mock a argparse namespace
        # https://stackoverflow.com/a/51197422/7410886
        self.config = SimpleNamespace(
            format=None,
            frontmatter=None,
            global_resource_folder=None,
            print_tree=False,
            exclude_notes=None,
            exclude_notes_with_tags=None,
            exclude_tags=None,
            include_notes=None,
            include_notes_with_tags=None,
            include_tags=None,
            no_progress_bars=True,
        )

    def assert_dir_trees_equal(self, dir1: Path, dir2: Path):
        """Check that two directories are equal, including file contents."""
        self.assertTrue(dir1.exists(), dir1)
        self.assertTrue(dir2.exists(), dir2)

        differences = []

        def compare_dirs(dir1: Path, dir2: Path):
            dirs_cmp = filecmp.dircmp(dir1, dir2)

            if dirs_cmp.left_only:
                differences.append(f"Only in {dir1}: {dirs_cmp.left_only}")

            if dirs_cmp.right_only:
                differences.append(f"Only in {dir2}: {dirs_cmp.right_only}")

            for file_ in dirs_cmp.diff_files:
                differences.append(
                    f"Different content: {dir1 / file_} - {dir2 / file_}"
                )
                if file_.endswith(".md"):
                    # detailed diff for markdown files
                    diff = difflib.unified_diff(
                        (dir1 / file_).read_text(encoding="utf-8").split("\n"),
                        (dir2 / file_).read_text(encoding="utf-8").split("\n"),
                    )
                    differences.append("\n".join(list(diff)[2:]))

            for common_dir in dirs_cmp.common_dirs:
                compare_dirs(dir1 / common_dir, dir2 / common_dir)

        compare_dirs(dir1, dir2)

        if differences:
            self.fail("\n".join(differences))

    @parameterized.expand(
        [
            [["bear/test_1/backup.bear2bk"]],
            [["bear/test_2/backup-2.bear2bk"]],
            [["cacher/test_1/cacher-export-202406182304.json"]],
            [["cherrytree/test_1/cherry.ctb.ctd"]],
            [["cherrytree/test_2/cherrytree_manual.ctd"]],
            [["cherrytree/test_3/lab_report.ctd"]],
            [["cherrytree/test_4/notes.ctd"]],
            [["clipto/test_1/clipto_backup_240401_105154.json"]],
            [["day_one/test_1/Day.One.zip"]],
            [["day_one/test_2/dayone-to-obsidian.zip"]],
            [["day_one/test_3/Export-Tagebuch.zip"]],
            [["dynalist/test_1/dynalist-backup-2024-04-12.zip"]],
            [["google_docs/test_1/takeout-20240929T124909Z-001.zip"]],
            [["google_keep/test_1/takeout-20241002T163525Z-001.tgz"]],
            [["google_keep/test_2/takeout-20240920T140112Z-001.zip"]],
            [["joplin/test_1/29_04_2024.jex"]],
            [["jrnl/test_1/myjournal.json"]],
            [["nimbus_note/test_1/Food"]],
            [["notion/test_1/7acd77c1-0197-44e3-9793-ae81ab520ac9_Export.zip"]],
            [["notion/test_2/export-testexport-nofolders.zip"]],
            [["obsidian/test_1"]],
            [["qownnotes/test_1"]],
            [["rednotebook/test_1/data"]],
            [["rednotebook/test_2/RedNotebook-Backup-2024-09-15.zip"]],
            [["simplenote/test_1/notes.zip"]],
            [["standard_notes/test_1/Standard Notes - Sun Apr 28 2024 12_56_55.zip"]],
            [["synology_note_station/test_1/20240331_144226_11102_Lagavulin.nsx"]],
            [["synology_note_station/test_2/20240409_202124_7594_Lagavulin.nsx"]],
            [["synology_note_station/test_3/notestation-test-books.nsx"]],
            [["synology_note_station/test_4/test.nsx"]],
            [["textbundle/test_1/textpack_example/example.textpack"]],
            [["textbundle/test_2/Bug report in tables_bear.textbundle"]],
            [["textbundle/test_3/Python CHP NOTES.textbundle"]],
            [["textbundle/test_4/Textbundle Example v1.textbundle"]],
            [["textbundle/test_5/Textbundle Example v2.textbundle"]],
            # [["tiddlywiki/test_1/tiddlers.json"]],
            [["tomboy_ng/test_1/gnote"]],
            [["tomboy_ng/test_2/tomboy-ng"]],
            [["zettelkasten/test_1/test_zettelkasten.zkn3"]],
            [["zoho_notebook/test_1/Notebook_14Apr2024_1300_html.zip"]],
        ],
        name_func=name_func,
    )
    def test_formats(self, test_input):
        """Test the conversion of custom formats to Markdown."""
        test_input = [Path(i) for i in test_input]
        # can be multiple
        test_data = [Path("test/data/test_data") / i for i in test_input]
        for datum in test_data:
            if not datum.exists():
                self.skipTest(f"No test data available at {datum}")

        test_data_output = Path("tmp_output") / test_input[0].parent
        shutil.rmtree(test_data_output, ignore_errors=True)
        reference_data = Path("test/data/reference_data") / test_input[0].parent

        self.config.input = test_data
        self.config.format = test_input[0].parts[0]
        self.config.output_folder = test_data_output
        jimmy.jimmy(self.config)

        # Skip only here to catch potential errors during conversion.
        if not reference_data.exists():
            self.skipTest(f"No reference data available at {reference_data}")

        self.assert_dir_trees_equal(test_data_output, reference_data)

    @parameterized.expand(
        [
            ["single_folder", ["default_format/arbitrary_folder"]],
            ["multiple_folders", ["default_format/arbitrary_folder"] * 2],
            ["single_file", ["default_format/arbitrary_folder/plaintext.txt"]],
            ["multiple_files", ["default_format/arbitrary_folder/plaintext.txt"] * 2],
            ["markdown_file", ["default_format/arbitrary_folder/sample.md"]],
        ]
    )
    def test_default_format(self, test_name, test_input):
        """Test the default format conversion to Markdown."""
        test_input = [Path(i) for i in test_input]
        # can be multiple
        test_data = [Path("test/data/test_data") / i for i in test_input]

        test_data_output = Path("tmp_output/default_format") / test_name
        shutil.rmtree(test_data_output, ignore_errors=True)
        # separate folder for each input
        reference_data = Path("test/data/reference_data/default_format") / test_name

        self.config.input = test_data
        self.config.output_folder = test_data_output
        jimmy.jimmy(self.config)

        if len(test_input) == 1:
            self.assert_dir_trees_equal(test_data_output, reference_data)
        else:
            for index in range(len(test_input)):
                actual_data = test_data_output.parent / (
                    test_data_output.name + f" {index}"
                )
                reference = reference_data.parent / (reference_data.name + f" {index}")
                self.assert_dir_trees_equal(actual_data, reference)

    @parameterized.expand(["all", "joplin", "obsidian"])
    def test_frontmatter(self, frontmatter):
        """Test the frontmatter generation."""

        test_data = [Path("test/data/test_data/joplin/test_1/29_04_2024.jex")]
        test_data_output = Path("tmp_output/frontmatter") / frontmatter
        shutil.rmtree(test_data_output, ignore_errors=True)
        # separate folder for each input
        reference_data = Path("test/data/reference_data/frontmatter") / frontmatter

        self.config.input = test_data
        self.config.format = "joplin"
        self.config.output_folder = test_data_output
        self.config.frontmatter = frontmatter
        jimmy.jimmy(self.config)

        self.assert_dir_trees_equal(test_data_output, reference_data)
