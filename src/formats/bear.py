"""Convert bear notes to the intermediate format."""

from pathlib import Path

import converter
from formats.textbundle import Converter as TextbundleConverter


class Converter(converter.BaseConverter):
    accepted_extensions = [".bear2bk"]

    def convert(self, file_or_folder: Path):
        # TODO: handle "tags.json"
        # file_dict = json.loads(file_or_folder.read_text(encoding="utf-8"))

        # see BaseConverter.convert_multiple()
        textbundle_converter = TextbundleConverter(self.format, self.output_folder)
        textbundle_converter.root_notebook = self.root_notebook
        for textbundle in sorted(self.root_path.glob("*.textbundle")):
            # TODO: handle info.json metadata
            textbundle_converter.root_path = textbundle_converter.prepare_input(
                textbundle
            )
            textbundle_converter.convert(textbundle)
