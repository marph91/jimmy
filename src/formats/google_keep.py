"""Convert Google Keep notes to the intermediate format."""

import datetime as dt
from pathlib import Path
import json

import converter
import intermediate_format as imf


class Converter(converter.BaseConverter):
    accepted_extensions = [".tgz", ".zip"]

    def convert(self, file_or_folder: Path):
        # take only the exports in json format
        for file_ in self.root_path.rglob("*.json"):
            note_keep = json.loads(Path(file_).read_text(encoding="utf-8"))

            title = note_keep.get("title", "")
            self.logger.debug(f'Converting note "{title}"')

            tags_keep = [
                label["name"]
                for label in note_keep.get("labels", [])
                if "name" in label
            ]
            if note_keep.get("isPinned"):
                tags_keep.append("google-keep-pinned")

            resources_keep = []
            for resource_keep in note_keep.get("attachments", []):
                resources_keep.append(
                    imf.Resource(file_.parent.absolute() / resource_keep["filePath"])
                )

            note_imf = imf.Note(
                title,
                note_keep.get("textContent", note_keep.get("textContentHtml", "")),
                source_application=self.format,
                # Labels / tags don't have a separate id. Just use the name as id.
                tags=[imf.Tag(tag) for tag in tags_keep],
                resources=resources_keep,
            )
            if (value := note_keep.get("createdTimestampUsec")) is not None:
                note_imf.created = dt.datetime.utcfromtimestamp(value // (10**6))
            if (value := note_keep.get("userEditedTimestampUsec")) is not None:
                note_imf.updated = dt.datetime.utcfromtimestamp(value // (10**6))
            self.root_notebook.child_notes.append(note_imf)
