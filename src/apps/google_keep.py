"""Convert Google Keep notes to the intermediate format."""

from pathlib import Path
import json

import common
import converter
import intermediate_format as imf


class Converter(converter.BaseConverter):

    def prepare_input(self, input_: Path) -> Path | None:
        match input_.suffix.lower():
            case ".zip":
                return common.extract_zip(input_)
            case ".tgz":
                return common.extract_tar(input_)
            case _:
                self.logger.error(f"Unsupported format for {self.app}")
                return None

    def convert(self, file_or_folder: Path):
        self.root_path = self.prepare_input(file_or_folder)
        if self.root_path is None:
            return

        # take only the exports in json format
        for file_ in self.root_path.glob("**/*.json"):
            note_keep = json.loads(Path(file_).read_text(encoding="UTF-8"))
            tags_keep = [label["name"] for label in note_keep.get("labels", [])]
            resources_keep = []
            for resource_keep in note_keep.get("attachments", []):
                resources_keep.append(
                    imf.Resource(file_.parent.absolute() / resource_keep["filePath"])
                )
            note_joplin = imf.Note(
                {
                    "title": note_keep["title"],
                    "body": note_keep["textContent"],
                    "user_created_time": note_keep["userEditedTimestampUsec"] // 1000,
                    "user_updated_time": note_keep["userEditedTimestampUsec"] // 1000,
                    "source_application": self.app,
                },
                # Labels / tags don't have a separate id. Just use the name as id.
                tags=[imf.Tag({"title": tag}) for tag in tags_keep],
                resources=resources_keep,
            )
            self.root_notebook.child_notes.append(note_joplin)
