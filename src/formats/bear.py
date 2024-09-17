"""Convert bear notes to the intermediate format."""

from pathlib import Path

import common
import converter
from formats.textbundle import Converter as TextbundleConverter


class Converter(converter.BaseConverter):
    accepted_extensions = [".bear2bk"]

    def prepare_input(self, input_: Path) -> Path:
        temp_folder = common.extract_zip(input_)
        return common.get_single_child_folder(temp_folder)

    def convert(self, file_or_folder: Path):
        self.root_path = self.prepare_input(file_or_folder)

        # TODO: handle "tags.json"
        # file_dict = json.loads(file_or_folder.read_text(encoding="utf-8"))

        # see BaseConverter.convert_multiple()
        textbundle_converter = TextbundleConverter(self.format, self.output_folder)
        textbundle_converter.root_notebook = self.root_notebook
        for textbundle in self.root_path.glob("*.textbundle"):
            # TODO: handle info.json metadata
            textbundle_converter.convert(textbundle)
