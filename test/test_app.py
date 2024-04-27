from dataclasses import dataclass
import json
from pathlib import Path
import unittest
import zipfile

from parameterized import parameterized
import requests

import jimmy


@dataclass
class Config:
    path: Path
    inputs: list[Path]
    expected_output: dict
    name: str | None = None

    @property
    def app(self):
        return self.path.parent.stem

    @property
    def expected_output_class(self):
        return jimmy.Stats(**self.expected_output)


def get_stats(inputs, app):
    note_tree = jimmy.convert_all_inputs(inputs, app)
    return jimmy.get_import_stats(note_tree)


TEST_CASES = []
TEST_CASE_FOLDER = Path(".cache")
TEST_CASE_FOLDER.mkdir(exist_ok=True)


def download_from_dropbox():
    # download
    # https://stackoverflow.com/a/20243081/7410886
    dropbox_url = "https://www.dropbox.com/scl/fo/pr7ccygc551haq4g7sovi/ACLJMNpwtbctRAS2EiWmizg?rlkey=hj59vfgka3nqcgng7emcsgldp&st=2v2zz8xa&dl=1"
    response = requests.get(dropbox_url)

    test_case_file = TEST_CASE_FOLDER / "test_cases.zip"
    if not test_case_file.exists():
        test_case_file.write_bytes(response.content)
        # unzip
        with zipfile.ZipFile(test_case_file) as zip_ref:
            zip_ref.extractall(TEST_CASE_FOLDER)
    find_test_configs()


def find_test_configs():
    global TEST_CASES
    # find test cases
    for testcase in TEST_CASE_FOLDER.rglob("testcases.json"):
        testcases_app = json.loads(testcase.read_text(encoding="UTF-8"))
        for testcase_app in testcases_app:
            TEST_CASES.append(Config(testcase, **testcase_app))


# needs to be executed before "parameterized"
download_from_dropbox()


def name_func(testcase_func, param_num, param):
    config = param[0][0]
    test_name = config.name or config.inputs[0].replace(".", "_")
    return f"{testcase_func.__name__}_{config.app}_{test_name}"


class IntermediateFormat(unittest.TestCase):

    @parameterized.expand(TEST_CASES, name_func=name_func)
    def test_convert(self, testcase):

        stats = get_stats(
            [testcase.path.parent / input_ for input_ in testcase.inputs], testcase.app
        )
        self.assertEqual(stats, testcase.expected_output_class)
