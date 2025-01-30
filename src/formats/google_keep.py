"""Convert Google Keep notes to the intermediate format."""

from pathlib import Path
import json

import common
import converter
import intermediate_format as imf
import markdown_lib.common


class Converter(converter.BaseConverter):
    accepted_extensions = [".tgz", ".zip"]

    @common.catch_all_exceptions
    def convert_note(self, file_: Path):
        note_keep = json.loads(file_.read_text(encoding="utf-8"))

        title = note_keep.get("title", "")
        if not title.strip():
            title = common.unique_title()
        self.logger.debug(f'Converting note "{title}"')

        note_imf = imf.Note(title, source_application=self.format)

        note_imf.tags = [
            imf.Tag(label["name"])
            for label in note_keep.get("labels", [])
            if "name" in label
        ]
        if note_keep.get("isPinned"):
            note_imf.tags.append(imf.Tag("google-keep-pinned"))

        for resource_keep in note_keep.get("attachments", []):
            note_imf.resources.append(
                imf.Resource(file_.parent.absolute() / resource_keep["filePath"])
            )

        # fall back to HTML if there is no plain text
        if "textContent" in note_keep:
            note_imf.body = note_keep["textContent"]
        elif (body_html := note_keep.get("textContentHtml")) is not None:
            note_imf.body = markdown_lib.common.markup_to_markdown(body_html)
        elif (body_list := note_keep.get("listContent")) is not None:
            # task list
            list_items_md = []
            for item in body_list:
                bullet = "- [x] " if item["isChecked"] else "- [ ] "
                list_items_md.append(f"{bullet}{item["text"]}")
            note_imf.body = "\n".join(list_items_md)
        else:
            note_imf.body = ""
            self.logger.debug("Couldn't obtain note body.")
        if (annotations := note_keep.get("annotations")) is not None:
            annotations_md = ["", "", "## Annotations", ""]
            for annotation in annotations:
                annotations_md.append(f"- <{annotation["url"]}>: {annotation["title"]}")
            annotations_md.append("")  # newline at the end
            note_imf.body += "\n".join(annotations_md)

        if (value := note_keep.get("createdTimestampUsec")) is not None:
            note_imf.created = common.timestamp_to_datetime(value // (10**6))
        if (value := note_keep.get("userEditedTimestampUsec")) is not None:
            note_imf.updated = common.timestamp_to_datetime(value // (10**6))
        self.root_notebook.child_notes.append(note_imf)

    def convert(self, file_or_folder: Path):
        # take only the exports in json format
        for file_ in sorted(self.root_path.rglob("*.json")):
            self.convert_note(file_)
