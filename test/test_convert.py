import difflib
import filecmp
import os
from pathlib import Path
import py7zr
from types import SimpleNamespace
import random
import shutil
import unittest

from parameterized import parameterized

import jimmy.main


def name_func(testcase_func, param_num, param):
    return f"{testcase_func.__name__}_{Path(param[0][0][0]).parent}"


class EndToEnd(unittest.TestCase):
    def setUp(self):
        import logging
        from rich.logging import RichHandler

        console_handler_formatter = logging.Formatter("%(message)s")
        console_handler = RichHandler(markup=True, show_path=False)
        console_handler.setFormatter(console_handler_formatter)
        console_handler.setLevel("DEBUG")
        jimmy.main.setup_logging(custom_handlers=[console_handler])

        jimmy.main.add_binaries_to_path()

        # use the same seed before every test to get reproducible uuids
        random.seed(42)

        # mock a argparse namespace
        # https://stackoverflow.com/a/51197422/7410886
        test_name = unittest.TestCase.id(self)
        if "colornote" in test_name:
            password = "1234"
        elif "evernote" in test_name:
            password = "password"
        else:
            password = None

        self.config = SimpleNamespace(
            format=None,
            password=password,
            frontmatter=None,
            template_file=None,
            global_resource_folder=None,
            local_resource_folder=Path("."),
            local_image_folder=None,
            max_name_length=50,
            print_tree=False,
            exclude_notes=None,
            exclude_notes_with_tags=None,
            exclude_tags=None,
            include_notes=None,
            include_notes_with_tags=None,
            include_tags=None,
        )

    def assert_dir_trees_equal(self, dir1: Path, dir2: Path):
        """Check that two directories are equal, including file contents."""
        self.assertTrue(dir1.exists(), f'Directory "{dir1}" does not exist.')
        self.assertTrue(dir2.exists(), f'Directory "{dir2}" does not exist.')

        differences = []

        def compare_dirs(dir1: Path, dir2: Path):
            dirs_cmp = filecmp.dircmp(dir1, dir2)

            if dirs_cmp.left_only:
                # .absolute().as_uri() needed for URI with spaces
                differences.append(f"Only in {dir1.absolute().as_uri()}: {dirs_cmp.left_only}")

            if dirs_cmp.right_only:
                differences.append(f"Only in {dir2.absolute().as_uri()}: {dirs_cmp.right_only}")

            for file_ in dirs_cmp.diff_files:
                differences.append(
                    f"Different content: {(dir1 / file_).absolute().as_uri()} - "
                    f"{(dir2 / file_).absolute().as_uri()}"
                )
                if file_.endswith(".md"):
                    # detailed diff for markdown files
                    diff = list(
                        difflib.unified_diff(
                            (dir1 / file_).read_text(encoding="utf-8").split("\n"),
                            (dir2 / file_).read_text(encoding="utf-8").split("\n"),
                        )
                    )
                    if diff:
                        differences.append("\n".join(list(diff)[2:]))
                    else:
                        differences.append(
                            'No difference detected. Check line endings with "cat -e"'
                        )

            for common_dir in dirs_cmp.common_dirs:
                compare_dirs(dir1 / common_dir, dir2 / common_dir)

        compare_dirs(dir1, dir2)

        if differences:
            self.fail("\n".join(differences))

    def format_test(self, test_input: Path):
        if len(test_input.parts) != 3:
            self.fail(
                'Test data should be in folder "<format>/test_<index>/<data>". '
                "Look at the other tests for examples."
            )

        # can be multiple
        test_data = [Path("test/data/test_data") / test_input]
        for datum in test_data:
            if not datum.exists():
                self.skipTest(f"No test data available at {datum}")

        test_data_output = Path("tmp_output") / test_input.parent
        shutil.rmtree(test_data_output, ignore_errors=True)
        reference_data = Path("test/data/reference_data") / test_input.parent

        if "frontmatter" in str(test_input):
            self.config.frontmatter = "joplin"
        self.config.input = test_data
        self.config.format = test_input.parts[0]
        self.config.output_folder = test_data_output
        jimmy.main.run_conversion(self.config)

        # Skip only here to catch potential errors during conversion.
        if not reference_data.exists():
            self.skipTest(f'No reference data available at "{reference_data.resolve()}"')

        self.assert_dir_trees_equal(test_data_output, reference_data)

    @parameterized.expand(
        [
            [["anki/test_1/MEILLEUR_DECK_ANGLAIS_3000.apkg"]],
            [["anki/test_2/Ukrainian_Prepositions_pictsaudio_ENG-UA__UA-ENG.apkg"]],
            [["anki/test_3/Hebrew_Alphabet_with_vowels.apkg"]],
            [["anytype/test_1/Anytype.20241112.175339.64"]],
            [["anytype/test_2/Anytype.20241113.215524.09.zip"]],
            [["bear/test_1_frontmatter/backup.bear2bk"]],
            [["bear/test_2/backup-2.bear2bk"]],
            [["bear/test_3/Bear Notes 2025-05-28 at 19.06.bear2bk"]],
            [["cacher/test_1_frontmatter/cacher-export-202406182304.json"]],
            [["cherrytree/test_1_frontmatter/cherry.ctb.ctd"]],
            [["cherrytree/test_2/cherrytree_manual.ctd"]],
            [["cherrytree/test_3/lab_report.ctd"]],
            [["cherrytree/test_4/various_sources"]],
            [["cherrytree/test_5/Learning-Resources-Cherry-Tree"]],
            [["cherrytree/test_6/practice"]],
            [["cherrytree/test_7/ZZZZZZ--table_test.ctd"]],
            [["clipto/test_1_frontmatter/clipto_backup_240401_105154.json"]],
            [["colornote/test_1_frontmatter/colornote-20241014.backup"]],
            [["day_one/test_1_frontmatter/Day.One.zip"]],
            [["day_one/test_2/dayone-to-obsidian.zip"]],
            [["day_one/test_3/Export-Tagebuch.zip"]],
            [["diaro/test_1_frontmatter/Diaro_20250821.zip"]],
            [["drafts/test_1_frontmatter/Drafts-2025-09-21-21-50.draftsExport"]],
            [["dynalist/test_1_frontmatter/dynalist-backup-2024-04-12.zip"]],
            [["evernote/test_1_frontmatter/obsidian-importer"]],
            [["evernote/test_2/joplin"]],
            [["evernote/test_3/yarle"]],
            [["evernote/test_4/Manuals.enex"]],
            [["google_docs/test_1/takeout-20240929T124909Z-001.zip"]],
            [["google_keep/test_1_frontmatter/takeout-20250130T150824Z-001.tgz"]],
            [["google_keep/test_2/takeout-20240920T140112Z-001.zip"]],
            [["google_keep/test_4/takeout2.zip"]],
            [["joplin/test_1_frontmatter/29_04_2024.jex"]],
            [["jrnl/test_1_frontmatter/myjournal.json"]],
            # [["nimbus_note/test_1/nimbus-export.zip"]],
            [["nimbus_note/test_2_frontmatter/Demo Workspace"]],
            [["notion/test_1_frontmatter/7acd77c1-0197-44e3-9793-ae81ab520ac9_Export.zip"]],
            [["notion/test_2/testexport-nofolders.zip"]],
            # unzipped zip, HTML
            [["notion/test_3/Archive.zip"]],
            # unzipped zip, HTML
            [["notion/test_4/cb177660-18fe-45a8-b1dd-b07f44a8af5e_Export.zip"]],
            # same as test 1, but HTML
            [["notion/test_5/67e39a7b-e75e-4dcb-9181-56ce222d3430_Export.zip"]],
            [["notion/test_6/notion-testspace.zip"]],
            [["obsidian/test_1_frontmatter/vault"]],
            [["onenote/test_1_frontmatter/OneDrive_2025-09-28.zip"]],
            [["onenote/test_2/onenoters"]],
            # can't test with frontmatter - git doesn't preserve timestamps
            # https://github.com/actions/checkout/issues/364#issuecomment-812618265
            [["qownnotes/test_1/note_folder"]],
            [["rednotebook/test_1_frontmatter/data"]],
            [["rednotebook/test_2/RedNotebook-Backup-2024-09-15.zip"]],
            [["roam_research/test_1_frontmatter/small-test-graph.json"]],
            [["roam_research/test_2/help-graph.json"]],
            [["roam_research/test_3/roam-to-git-demo-2025-04-15-12-05-52.json"]],
            [["simplenote/test_1_frontmatter/notes.zip"]],
            [["simplenote/test_2/notes_1.zip"]],
            [["simplenote/test_3/simplenote.zip"]],
            [["standard_notes/test_1_frontmatter/Standard Notes - Sun Apr 28 2024 12_56_55.zip"]],
            [["standard_notes/test_2/Standard.Notes.-.super_format.GMT+0100.zip"]],
            [["standard_notes/test_3/backup.zip"]],
            [["standard_notes/test_4/SN-Empty-SuperNote-Backup.zip"]],
            [["standard_notes/test_5/Standard Notes - Fri Jan 14 2022 10_31_29.zip"]],
            [["standard_notes/test_6/Standard Notes - Tue Aug 29 2023 08_51_11.zip"]],
            [["synology_note_station/test_1/20240331_144226_11102_Lagavulin.nsx"]],
            [["synology_note_station/test_2/20240409_202124_7594_Lagavulin.nsx"]],
            [["synology_note_station/test_3_frontmatter/notestation-test-books.nsx"]],
            [["synology_note_station/test_4/test.nsx"]],
            [["synology_note_station/test_5/20241005_184010_8701_demouser.nsx"]],
            # can't test with frontmatter - git doesn't preserve timestamps
            # https://github.com/actions/checkout/issues/364#issuecomment-812618265
            [["textbundle/test_1/example.textpack"]],
            [["textbundle/test_2/Bug report in tables_bear.textbundle"]],
            [["textbundle/test_3/Python CHP NOTES.textbundle"]],
            [["textbundle/test_4/Textbundle Example v1.textbundle"]],
            [["textbundle/test_5/Textbundle Example v2.textbundle"]],
            [["textbundle/test_6/multiple_files"]],
            # a subset of test_1 is in test_5
            # [["tiddlywiki/test_1/tiddlers.json"]],
            [["tiddlywiki/test_2_frontmatter/deserializers"]],
            [["tiddlywiki/test_3/Plugins.tid"]],
            [["tiddlywiki/test_4/html_folder"]],
            [["tiddlywiki/test_5/tiddlers.json"]],
            [["tiddlywiki/test_6/daniel-spurious-alerts.json"]],
            [["tomboy_ng/test_1_frontmatter/gnote"]],
            [["tomboy_ng/test_2/tomboy-ng"]],
            [["turtl/test_1_frontmatter/turtl-backup.json"]],
            [["upnote/test_1_frontmatter/new_user"]],
            [["wordpress/test_1_frontmatter/mywordpresswebsite.WordPress.2024-12-17.xml"]],
            [["wordpress/test_2/testing.wordpress.xml"]],
            [["wordpress/test_3/wp.xml"]],
            [["wordpress/test_4/adversarial-example.xml"]],
            [["zettelkasten/test_1_frontmatter/test_zettelkasten.zkn3"]],
            [["zim/test_1_frontmatter/notebook"]],
            [["zim/test_2/Zim-Sample-Notebook"]],
            [["zim/test_3/doc"]],
            [["zoho_notebook/test_1_frontmatter/Notebook_18Jan2025_1756_html.zip"]],
            # [["zoho_notebook/test_2/Notebook_02Mar2022_0441_znote.zip"]],
            # [["zoho_notebook/test_3/Notebook_14Apr2024_0732_znote.zip"]],
        ],
        name_func=name_func,
    )
    def test_formats(self, test_input: str):
        """Test the conversion of custom formats to Markdown."""
        self.format_test(Path(test_input[0]))

    @parameterized.expand(
        [
            [["google_keep/test_3_encrypted/takeout-20250123T101543Z-001.zip"]],
            [["synology_note_station/test_6_encrypted/test8.nsx"]],
            [["synology_note_station/test_7_encrypted/test10.nsx"]],
            [["telegram/test_1_encrypted/DataExport_2025-03-24"]],
        ],
        name_func=name_func,
    )
    def test_formats_encrypted(self, test_input: str):
        """Test the conversion of custom formats to Markdown."""
        password = os.getenv("JIMMY_TEST_PASSWORD")
        if password is None:
            self.skipTest('Need password for encrypted test data at "JIMMY_TEST_PASSWORD"')

        # Pythons zipfile doesn't support AES256 encryption. Use "py7zr" instead.
        test_input = Path(test_input[0])
        test_input_path = Path("test/data/test_data") / test_input.parent
        if not test_input_path.exists():
            with py7zr.SevenZipFile(
                test_input_path.with_suffix(".7z"), password=password
            ) as encrypted_7z:
                encrypted_7z.extractall(path=test_input_path.parent)

        reference_data_path = Path("test/data/reference_data") / test_input.parent
        if not reference_data_path.exists() and reference_data_path.with_suffix(".7z").exists():
            with py7zr.SevenZipFile(
                reference_data_path.with_suffix(".7z"), password=password
            ) as encrypted_7z:
                encrypted_7z.extractall(path=reference_data_path.parent)

        self.format_test(test_input)

    @parameterized.expand(
        [
            ["single_folder", ["default_format/arbitrary_folder"]],
            ["multiple_folders", ["default_format/arbitrary_folder"] * 2],
            ["single_file", ["default_format/arbitrary_folder/plaintext.txt"]],
            ["multiple_files", ["default_format/arbitrary_folder/plaintext.txt"] * 2],
            ["markdown_file", ["default_format/arbitrary_folder/sample.md"]],
            ["asciidoc", ["default_format/asciidoc"]],
            # TODO: bbcode
            ["eml", ["default_format/eml"]],
            ["html", ["default_format/html"]],
            ["latex", ["default_format/latex"]],
            ["mediawiki", ["default_format/mediawiki"]],
            ["odt", ["default_format/odt"]],
            ["samsung_notes", ["default_format/samsung_notes"]],
            ["txt2tags", ["default_format/txt2tags-2"]],
            ["vimwiki", ["default_format/vimwiki"]],
        ]
    )
    def test_default_format(self, test_name, test_input):
        """Test the default format conversion to Markdown."""
        test_input = [Path(i) for i in test_input]
        # can be multiple
        test_data = [Path("test/data/test_data") / i for i in test_input]

        test_data_output = Path("tmp_output/default_format") / test_name
        # Can be multiple output folders. Delete all.
        for folder in test_data_output.parent.glob(f"{test_data_output.name}*"):
            shutil.rmtree(folder, ignore_errors=True)
        # separate folder for each input
        reference_data = Path("test/data/reference_data/default_format") / test_name

        self.config.input = test_data
        self.config.output_folder = test_data_output
        jimmy.main.run_conversion(self.config)

        if len(test_input) == 1:
            self.assert_dir_trees_equal(test_data_output, reference_data)
        else:
            for index in range(len(test_input)):
                actual_data = test_data_output.parent / (test_data_output.name + f" {index}")
                reference = reference_data.parent / (reference_data.name + f" {index}")
                self.assert_dir_trees_equal(actual_data, reference)

    @parameterized.expand(
        [
            "joplin",
            "obsidian",
            "custom_frontmatter.txt",
            "table.txt",
            "title_heading.txt",
        ]
    )  # qownnotes == obsidian (tags only)
    def test_template(self, template):
        """Test note body templates and frontmatter."""

        test_data = [Path("test/data/test_data/template") / Path(template).stem]
        test_data_output = Path("tmp_output/template")
        shutil.rmtree(test_data_output / Path(template).stem, ignore_errors=True)
        # separate folder for each input
        reference_data = Path("test/data/reference_data/template") / Path(template).stem

        self.config.input = test_data
        self.config.output_folder = test_data_output
        if template in ("joplin", "obsidian"):
            self.config.frontmatter = template
            self.config.template_file = None
        else:
            self.config.frontmatter = None
            self.config.template_file = (Path("test/data/test_data/template") / template).resolve()
        jimmy.main.run_conversion(self.config)

        self.assert_dir_trees_equal(test_data_output / Path(template).stem, reference_data)

    @parameterized.expand(
        [
            ["global", {"global_resource_folder": Path("res")}],
            [
                "global_forbidden",
                {"global_resource_folder": Path("r:es")},
            ],
            [
                "global_outside",
                {"global_resource_folder": Path("../res")},
            ],
            ["local_default", {"local_resource_folder": Path(".")}],  # default
            ["local", {"local_resource_folder": Path("res")}],
            [
                "local_forbidden",
                {"local_resource_folder": Path("re:s")},
            ],
            [
                "local_splitted",
                {
                    "local_resource_folder": Path("attachments"),
                    "local_image_folder": Path("media"),
                },
            ],
        ]
    )
    def test_attachment_folder(self, name, folder_options):
        """Test the attachment folders."""

        test_data = [Path("test/data/test_data/obsidian/test_1_frontmatter")]
        test_data_output = Path(f"tmp_output/attachment_folder/{name}")
        shutil.rmtree(test_data_output, ignore_errors=True)
        # separate folder for each input
        reference_data = Path(f"test/data/reference_data/attachment_folder/{name}")

        self.config.input = test_data
        self.config.format = "obsidian"
        self.config.output_folder = test_data_output
        for option, value in folder_options.items():
            setattr(self.config, option, value)
        jimmy.main.run_conversion(self.config)

        self.assert_dir_trees_equal(test_data_output, reference_data)
        if name == "global_outside":
            # outside root dir -> verify separately
            self.assert_dir_trees_equal(test_data_output / value, reference_data / value)
