"""Convert Google Docs documents to the intermediate format."""

from pathlib import Path

import common
import converter
from converter import DefaultConverter


class Converter(converter.BaseConverter):
    accepted_extensions = [".tgz", ".zip"]

    def prepare_input(self, input_: Path) -> Path:
        return common.extract_zip(input_)

    def convert(self, file_or_folder: Path):
        self.root_path = self.prepare_input(file_or_folder)

        # see BaseConverter.convert_multiple()
        docs_converter = DefaultConverter(self.format, self.output_folder)
        docs_converter.root_notebook = self.root_notebook
        docs_converter.convert(self.root_path / "Takeout/Drive")
