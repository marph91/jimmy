"""Convert cacher notes to the intermediate format."""

from collections import defaultdict
from pathlib import Path
import json
import logging

from common import iso_to_unix_ms
import converter
import intermediate_format as imf


LOGGER = logging.getLogger("jimmy")


class Converter(converter.BaseConverter):
    accepted_extensions = [".json"]

    def convert(self, file_or_folder: Path):
        file_dict = json.loads(file_or_folder.read_text(encoding="utf-8"))

        # Get the tags/labels for each note/snippet.
        # cacher labels == joplin tags
        tags_per_note = defaultdict(list)
        for label in file_dict["personalLibrary"]["labels"]:
            for assigned_snippets in label["snippets"]:
                # We can duplicate tags here. They get deduplicated at import.
                tags_per_note[assigned_snippets["guid"]].append(
                    imf.Tag({"title": label["title"]}, original_id=label["guid"])
                )

        # cacher snippets == joplin notebooks
        # cacher files == joplin notes
        for snippet in file_dict["personalLibrary"]["snippets"]:
            notebook = imf.Notebook(
                {
                    "title": snippet["title"],
                    "user_created_time": iso_to_unix_ms(snippet["createdAt"]),
                    "user_updated_time": iso_to_unix_ms(snippet["updatedAt"]),
                    "source_application": self.format,
                },
                original_id=snippet["guid"],
            )
            self.root_notebook.child_notebooks.append(notebook)

            for file_ in snippet["files"]:
                if file_["filetype"] != "markdown":
                    LOGGER.warning(
                        f"Ignoring file {file_['filename']}. "
                        "Only markdown supported for now."
                    )
                    continue
                note_joplin = imf.Note(
                    {
                        "title": Path(file_["filename"]).stem,
                        "body": file_["content"],
                        "user_created_time": iso_to_unix_ms(file_["createdAt"]),
                        "user_updated_time": iso_to_unix_ms(file_["updatedAt"]),
                        "source_application": self.format,
                    },
                    # Tags are assigned per snippet (not per file).
                    tags=tags_per_note.get(snippet["guid"], []),
                    original_id=file_["guid"],
                )
                notebook.child_notes.append(note_joplin)
