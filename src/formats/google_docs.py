"""Convert Google Docs documents to the intermediate format."""

from pathlib import Path

import converter
from converter import DefaultConverter


class Converter(converter.BaseConverter):
    accepted_extensions = [".tgz", ".zip"]

    def convert(self, file_or_folder: Path):
        # see BaseConverter.convert_multiple()
        docs_converter = DefaultConverter(self.format, self.output_folder)
        docs_converter.root_notebook = self.root_notebook
        docs_converter.root_path = self.root_path / "Takeout/Drive"
        docs_converter.convert(self.root_path / "Takeout/Drive")
