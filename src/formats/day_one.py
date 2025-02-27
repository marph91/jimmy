"""Convert Day One notes to the intermediate format."""

import datetime as dt
from pathlib import Path
import json

import common
import converter
import intermediate_format as imf
import markdown_lib.common


def guess_title(body: str) -> str:
    for line in body.split("\n"):
        if line.startswith("!["):
            continue
        if not line.strip():
            continue
        return line.lstrip("#").strip()
    return ""


class Converter(converter.BaseConverter):
    accepted_extensions = [".zip"]

    @staticmethod
    def create_notebook_hierarchy(
        date_: dt.datetime, root_notebook: imf.Notebook
    ) -> imf.Notebook:
        def find_or_create_child_notebook(
            title: str, parent_notebook: imf.Notebook
        ) -> imf.Notebook:
            for child_notebook in parent_notebook.child_notebooks:
                if child_notebook.title == title:
                    return child_notebook
            new_notebook = imf.Notebook(title)
            parent_notebook.child_notebooks.append(new_notebook)
            return new_notebook

        return find_or_create_child_notebook(date_.strftime("%Y-%m-%d"), root_notebook)

    def get_resource_maps(self, entries: list) -> dict[str, dict[str, Path]]:
        # Create "global" maps. The resources are attached to single entries, but they
        # can be referenced. For example when copying the same photo to another note,
        # the same photo gets another id. But both IDs are referenced at the first note
        # photos...
        # Dict of the actual maps.
        resource_id_filename_maps: dict[str, dict[str, Path]] = {
            "audios": {},
            "pdfAttachments": {},
            "photos": {},
            "videos": {},
        }

        for entry in entries:
            for json_key_name, actual_map in resource_id_filename_maps.items():
                folder_name = (
                    "pdfs" if json_key_name == "pdfAttachments" else json_key_name
                )
                for resource in entry.get(json_key_name, []):
                    potential_matches = list(
                        (self.root_path / folder_name).glob(f"{resource['md5']}.*")
                    )
                    if len(potential_matches) == 0:
                        self.logger.warning(
                            f"Couldn't find {folder_name} {resource['md5']}"
                        )
                    elif len(potential_matches) == 1:
                        actual_map[resource["identifier"]] = Path(potential_matches[0])
                    else:
                        self.logger.debug(f"Ambiguous {folder_name} {resource['md5']}")
                        actual_map[resource["identifier"]] = Path(potential_matches[0])

        return resource_id_filename_maps

    def handle_markdown_links(
        self, body: str, resource_id_filename_map: dict
    ) -> tuple[imf.Resources, imf.NoteLinks]:
        resources = []
        note_links = []

        def handle_resource(original_id: str, type_: str):
            if original_id not in resource_id_filename_map[type_]:
                self.logger.debug(f"Couldn't find audio with id {original_id}")
                return
            source_path = (
                self.root_path / type_ / resource_id_filename_map[type_][original_id]
            )
            if not source_path.is_file():
                return
            resources.append(imf.Resource(source_path, str(link), link.text))

        for link in markdown_lib.common.get_markdown_links(body):
            if link.is_web_link or link.is_mail_link:
                continue  # keep the original links
            if link.url.startswith("dayone://view?entryId="):
                # internal link
                original_id = link.url.replace("dayone://view?entryId=", "")
                note_links.append(imf.NoteLink(str(link), original_id, link.text))
            elif link.url.startswith("dayone2://view?entryId="):
                # internal link
                original_id = link.url.replace("dayone2://view?entryId=", "")
                note_links.append(imf.NoteLink(str(link), original_id, link.text))

            # photos, audios, pdfs and videos
            elif link.url.startswith("dayone-moment://"):
                original_id = link.url.replace("dayone-moment://", "")
                handle_resource(original_id, "photos")
            elif link.url.startswith("dayone-moment:/audio/"):
                original_id = link.url.replace("dayone-moment:/audio/", "")
                handle_resource(original_id, "audios")
            elif link.url.startswith("dayone-moment:/pdfAttachment/"):
                original_id = link.url.replace("dayone-moment:/pdfAttachment/", "")
                handle_resource(original_id, "pdfAttachments")
            elif link.url.startswith("dayone-moment:/video/"):
                original_id = link.url.replace("dayone-moment:/video/", "")
                handle_resource(original_id, "videos")
            else:
                self.logger.debug(f"Unknown URL protocol {link.url}")
        return resources, note_links

    @common.catch_all_exceptions
    def convert_note(
        self, entry, resource_id_filename_map, root_notebook: imf.Notebook
    ):
        note_body = entry.get("text", "")
        # Backslashes are added often. Removing them like this might cause issues.
        note_body = note_body.replace("\\", "")
        # https://stackoverflow.com/a/55400921/7410886
        note_body = note_body.replace("\u200b", "")

        title = guess_title(note_body)
        self.logger.debug(f'Converting note "{title}"')

        tags = entry.get("tags", [])
        if entry.get("starred"):
            tags.append("day-one-starred")
        if entry.get("pinned"):
            tags.append("day-one-pinned")

        resources, note_links = self.handle_markdown_links(
            note_body, resource_id_filename_map
        )

        note_imf = imf.Note(
            title,
            note_body,  # TODO: Is there any advantage of rich text?
            created=dt.datetime.fromisoformat(entry["creationDate"]),
            updated=dt.datetime.fromisoformat(entry["modifiedDate"]),
            source_application=self.format,
            resources=resources,
            tags=[imf.Tag(tag) for tag in tags],
            note_links=note_links,
            original_id=entry["uuid"],
        )

        if (location := entry.get("location")) is not None:
            note_imf.latitude = location["latitude"]
            note_imf.longitude = location["longitude"]

        creation_date = dt.datetime.fromisoformat(entry["creationDate"])
        parent_notebook = self.create_notebook_hierarchy(creation_date, root_notebook)
        parent_notebook.child_notes.append(note_imf)

    def convert(self, file_or_folder: Path):
        journals = list(self.root_path.glob("*.json"))
        if len(journals) == 0:
            self.logger.warning(
                "Couldn't find json file in the zip. Is this a Day One export?"
            )
            return

        for journal in journals:
            root_notebook = imf.Notebook(journal.stem)
            self.root_notebook.child_notebooks.append(root_notebook)

            file_dict = json.loads(journal.read_text(encoding="utf-8"))
            resource_id_filename_map = self.get_resource_maps(file_dict["entries"])
            for entry in file_dict["entries"]:
                # TODO: attach non-referenced photos, videos, audios, pdfAttachments?
                self.convert_note(entry, resource_id_filename_map, root_notebook)
