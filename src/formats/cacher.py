"""Convert cacher notes to the intermediate format."""

from collections import defaultdict
import datetime as dt
from pathlib import Path
import json

import converter
import intermediate_format as imf


class Converter(converter.BaseConverter):
    accepted_extensions = [".json"]

    def convert(self, file_or_folder: Path):
        file_dict = json.loads(file_or_folder.read_text(encoding="utf-8"))

        # Get the tags/labels for each note/snippet.
        # cacher labels == tags
        tags_per_note = defaultdict(list)
        for label in file_dict["personalLibrary"]["labels"]:
            for assigned_snippets in label["snippets"]:
                # We can duplicate tags here. They get deduplicated at import.
                tags_per_note[assigned_snippets["guid"]].append(
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

            for file_ in snippet["files"]:
                if file_["filetype"] != "markdown":
                    self.logger.warning(
                        f"Ignoring file {file_['filename']}. "
                        "Only markdown supported for now."
                    )
                    continue
                note_imf = imf.Note(
                    **{
                        "title": Path(file_["filename"]).stem,
                        "body": file_["content"],
                        "created": dt.datetime.fromisoformat(file_["createdAt"]),
                        "updated": dt.datetime.fromisoformat(file_["updatedAt"]),
                        "source_application": self.format,
                    },
                    # Tags are assigned per snippet (not per file).
                    tags=tags_per_note.get(snippet["guid"], []),
                    original_id=file_["guid"],
                )
                notebook.child_notes.append(note_imf)
