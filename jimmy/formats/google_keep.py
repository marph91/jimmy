"""Convert Google Keep notes to the intermediate format."""

from pathlib import Path
import json

from jimmy import common, converter, intermediate_format as imf
import jimmy.md_lib.convert


class Converter(converter.BaseConverter):
    @common.catch_all_exceptions
    def convert_note(self, file_: Path):
        note_keep = json.loads(file_.read_text(encoding="utf-8"))

        title = note_keep.get("title", "")
        if not title.strip():
            title = common.unique_title()
        self.logger.debug(f'Converting note "{title}"')

        note_imf = imf.Note(title, source_application=self.format)

        note_imf.tags = [
            imf.Tag(label["name"]) for label in note_keep.get("labels", []) if "name" in label
        ]
        if note_keep.get("isPinned"):
            note_imf.tags.append(imf.Tag("google-keep-pinned"))

        for resource_keep in note_keep.get("attachments", []):
            resource_path = file_.parent.absolute() / resource_keep["filePath"]
            if resource_path.is_file():
                note_imf.resources.append(imf.Resource(resource_path))
            elif (other_resource_path := common.try_other_suffixes(resource_path)) is not None:
                # last resort: sometimes the extension is changed and referenced incorrectly
                note_imf.resources.append(imf.Resource(other_resource_path))
            else:
                self.logger.warning(f'Resource "{resource_path}" does not exist.')

        # fall back to HTML if there is no plain text
        if "textContent" in note_keep:
            note_imf.body = note_keep["textContent"]
        elif (body_html := note_keep.get("textContentHtml")) is not None:
            note_imf.body = jimmy.md_lib.convert.markup_to_markdown(body_html, pwd=file_.parent)
        elif (body_list := note_keep.get("listContent")) is not None:
            # task list
            list_items_md = []
            for item in body_list:
                bullet = "- [x] " if item["isChecked"] else "- [ ] "
                list_items_md.append(f"{bullet}{item['text']}")
            note_imf.body = "\n".join(list_items_md)
        else:
            note_imf.body = ""
            self.logger.debug("Couldn't obtain note body.")
        if (annotations := note_keep.get("annotations")) is not None:
            annotations_md = ["", "", "## Annotations", ""]
            for annotation in annotations:
                annotations_md.append(f"- <{annotation['url']}>: {annotation['title']}")
            annotations_md.append("")  # newline at the end
            note_imf.body += "\n".join(annotations_md)

        if (value := note_keep.get("createdTimestampUsec")) is not None:
            note_imf.created = common.timestamp_to_datetime(value // (10**6))
        if (value := note_keep.get("userEditedTimestampUsec")) is not None:
            note_imf.updated = common.timestamp_to_datetime(value // (10**6))
        self.root_notebook.child_notes.append(note_imf)

    def convert(self, file_or_folder: Path):
        notes = list(self.root_path.rglob("*.json"))
        if len(notes) == 0:
            self.logger.warning("Couldn't find a json file. Is this really a Google Keep export?")
            return
        # take only the exports in json format
        for note in sorted(notes):
            self.convert_note(note)
