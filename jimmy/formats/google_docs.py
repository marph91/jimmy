"""Convert Google Docs documents to the intermediate format."""

from pathlib import Path

from jimmy import converter
from jimmy.converter import DefaultConverter


class Converter(converter.BaseConverter):
    accepted_extensions = [".tgz", ".zip"]

    def convert_note(self):
        pass

    def convert(self, file_or_folder: Path):
        # see BaseConverter.convert_multiple()
        docs_converter = DefaultConverter(self._config)
        docs_converter.root_notebook = self.root_notebook
        docs_converter.root_path = self.root_path / "Takeout/Drive"
        docs_converter.convert(self.root_path / "Takeout/Drive")
