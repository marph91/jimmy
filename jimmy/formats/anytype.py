"""Convert AnyType notes to the intermediate format."""

import os
from pathlib import Path

os.environ["TQDM_DISABLE"] = "1"  # disable tqdm progress bars in anytype

from anyblock_exporter import AnytypeConverter  # pylint: disable=import-error,wrong-import-position
from jimmy import common, converter  # pylint: disable=wrong-import-position


class Converter(converter.BaseConverter):
    accepted_extensions = [".zip"]
    accept_folder = True

    def convert_note(self):
        pass

    def convert(self, file_or_folder: Path):
        # TODO: fix duplicated nested output folder
        intermediate_markdown_folder = common.get_temp_folder() / self.output_folder

        anytype_converter = AnytypeConverter(
            self.root_path, intermediate_markdown_folder
        )
        anytype_converter.process_all_files()

        # read the markdown again to respect settings like a custom resource folder
        markdown_converter = converter.DefaultConverter(self._config)
        markdown_converter.root_notebook = self.root_notebook
        markdown_converter.convert(intermediate_markdown_folder)
