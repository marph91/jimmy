"""Convert cacher notes to the intermediate format."""

from collections import defaultdict
import datetime as dt
from pathlib import Path
import json

import common
import converter
import intermediate_format as imf


class Converter(converter.BaseConverter):
    accepted_extensions = [".json"]

    @common.catch_all_exceptions
    def convert_note(self, file_: dict, notebook: imf.Notebook, tags: imf.Tags):
        if file_["filetype"] != "markdown":
            self.logger.warning(
                f"Ignoring file {file_['filename']}. "
                "Only markdown supported for now."
            )
            return
        title = Path(file_["filename"]).stem
        self.logger.debug(f'Converting note "{title}"')
        note_imf = imf.Note(
            title,
            file_["content"],
            created=dt.datetime.fromisoformat(file_["createdAt"]),
            updated=dt.datetime.fromisoformat(file_["updatedAt"]),
            source_application=self.format,
            tags=tags,
            original_id=file_["guid"],
        )
        notebook.child_notes.append(note_imf)

    def convert(self, file_or_folder: Path):
        file_dict = json.loads(file_or_folder.read_text(encoding="utf-8"))

        # Get the tags/labels for each snippet.
        # cacher labels == tags
        tags_per_snippet = defaultdict(list)
        for label in file_dict["personalLibrary"]["labels"]:
            for assigned_snippets in label["snippets"]:
                # We can duplicate tags here. They get deduplicated at import.
                tags_per_snippet[assigned_snippets["guid"]].append(
                    imf.Tag(label["title"], original_id=label["guid"])
                )

        # cacher snippets == notebooks
        # cacher files == notes
        for snippet in file_dict["personalLibrary"]["snippets"]:
            notebook = imf.Notebook(
                snippet["title"],
                original_id=snippet["guid"],
            )
            self.root_notebook.child_notebooks.append(notebook)

            # Tags are assigned per snippet (not per file).
            tags = tags_per_snippet.get(snippet["guid"], [])
            for file_ in snippet["files"]:
                self.convert_note(file_, notebook, tags)
