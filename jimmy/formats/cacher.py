"""Convert cacher notes to the intermediate format."""

from collections import defaultdict
import datetime as dt
from pathlib import Path
import json

from jimmy import common, converter, intermediate_format as imf
import jimmy.md_lib.common


class Converter(converter.BaseConverter):
    accepted_extensions = [".json"]

    @common.catch_all_exceptions
    def convert_note(self, file_: dict, notebook: imf.Notebook, tags: imf.Tags):
        if file_["filetype"] != "markdown":
            self.logger.warning(
                f"Ignoring file {file_['filename']}. Only markdown supported for now."
            )
            return
        title = Path(file_["filename"]).stem
        self.logger.debug(f'Converting note "{title}"')

        _, body = jimmy.md_lib.common.split_title_from_body(file_["content"])
        note_imf = imf.Note(
            title,
            body,
            created=dt.datetime.fromisoformat(file_["createdAt"]),
            updated=dt.datetime.fromisoformat(file_["updatedAt"]),
            source_application=self.format,
            tags=tags,
            original_id=file_["guid"],
        )
        notebook.child_notes.append(note_imf)

    def convert(self, file_or_folder: Path):
        input_json = json.loads(file_or_folder.read_text(encoding="utf-8"))
        if "personalLibrary" not in input_json:
            self.logger.error(
                '"personalLibrary" not found. Is this really a cacher export?'
            )
            return

        # Get the tags/labels for each snippet.
        # cacher labels == tags
        tags_per_snippet = defaultdict(list)
        for label in input_json["personalLibrary"]["labels"]:
            for assigned_snippets in label["snippets"]:
                # We can duplicate tags here. They get deduplicated at import.
                tags_per_snippet[assigned_snippets["guid"]].append(
                    imf.Tag(label["title"], original_id=label["guid"])
                )

        # cacher snippets == notebooks
        # cacher files == notes
        for snippet in input_json["personalLibrary"]["snippets"]:
            notebook = imf.Notebook(
                snippet["title"],
                original_id=snippet["guid"],
            )
            self.root_notebook.child_notebooks.append(notebook)

            # Tags are assigned per snippet (not per file).
            tags = tags_per_snippet.get(snippet["guid"], [])
            for file_ in snippet["files"]:
                self.convert_note(file_, notebook, tags)
