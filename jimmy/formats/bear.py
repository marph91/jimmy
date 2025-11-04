"""Convert bear notes to the intermediate format."""

from pathlib import Path

from jimmy import converter
from jimmy.formats.textbundle import Converter as TextbundleConverter


class Converter(converter.BaseConverter):
    def convert_note(self):
        pass

    def convert(self, file_or_folder: Path):
        # "tags.json" is not needed. The tags are handled inside the textbundles.

        # see BaseConverter.convert_multiple()
        textbundle_config = self._config
        textbundle_config.format = "textbundle"
        textbundle_converter = TextbundleConverter(textbundle_config)
        textbundle_converter.root_notebook = self.root_notebook
        for textbundle in sorted(self.root_path.glob("*.textbundle")):
            textbundle_converter.root_path = textbundle_converter.prepare_input(textbundle)
            textbundle_converter.convert(textbundle)
