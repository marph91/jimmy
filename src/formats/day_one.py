"""Convert Day One notes to the intermediate format."""

import datetime as dt
from pathlib import Path
import json

import common
import converter
import intermediate_format as imf


def guess_title(body):
    for line in body.split("\n"):
        if line.startswith("!["):
            continue
        if not line.strip():
            continue
        return line.lstrip("#").strip()
    return ""


class Converter(converter.BaseConverter):
    accepted_extensions = [".zip"]

    def prepare_input(self, input_: Path) -> Path:
        return common.extract_zip(input_)

    def create_notebook_hierarchy(self, date_: dt.datetime) -> imf.Notebook:
        def find_or_create_child_notebook(title, parent_notebook):
            for child_notebook in parent_notebook.child_notebooks:
                if child_notebook.data["title"] == title:
                    return child_notebook
            new_notebook = imf.Notebook({"title": title})
            parent_notebook.child_notebooks.append(new_notebook)
            return new_notebook

        return find_or_create_child_notebook(
            date_.strftime("%Y-%m-%d"), self.root_notebook
        )

    def get_resource_maps(self, entries):
        # Create "global" maps. The resources are attached to single entries, but they
        # can be referenced. For example when copying the same photo to another note,
        # the same photo gets another id. But both IDs are referenced at the first note
        # photos...
        # Dict of the actual maps.
        resource_id_filename_maps: dict = {
            "audios": {},
            "pdfAttachments": {},
            "photos": {},
            "videos": {},
        }

        assert self.root_path is not None  # for mypy

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
    ) -> tuple[list, list]:
        resources = []
        note_links = []

        def handle_resource(original_id: str, type_: str):
            assert self.root_path is not None  # for mypy
            if original_id not in resource_id_filename_map[type_]:
                self.logger.warning(f"Couldn't find audio with id {original_id}")
                return
            source_path = (
                self.root_path / type_ / resource_id_filename_map[type_][original_id]
            )
            if not source_path.is_file():
                return
            resources.append(imf.Resource(source_path, str(link), link.text))

        for link in common.get_markdown_links(body):
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
                self.logger.warning(f"Unknown URL protocol {link.url}")
        return resources, note_links

    def convert(self, file_or_folder: Path):
        self.root_path = self.prepare_input(file_or_folder)

        potential_sources = list(self.root_path.glob("*.json"))
        if len(potential_sources) != 1:
            self.logger.warning(
                f"Found to many or less json files {len(potential_sources)}"
            )
            return

        file_dict = json.loads(potential_sources[0].read_text(encoding="utf-8"))

        resource_id_filename_map = self.get_resource_maps(file_dict["entries"])

        for entry in file_dict["entries"]:
            # TODO: attach non-referenced photos, videos, audios, pdfAttachments?

            note_body = entry.get("text", "")
            # Backslashes are added often. Removing them like this might cause issues.
            note_body = note_body.replace("\\", "")
            # https://stackoverflow.com/a/55400921/7410886
            note_body = note_body.replace("\u200b", "")

            note_data = {
                "title": guess_title(note_body),
                "body": note_body,  # TODO: Is there any advantage of rich text?
                "user_created_time": common.iso_to_unix_ms(entry["creationDate"]),
                "user_updated_time": common.iso_to_unix_ms(entry["modifiedDate"]),
                "source_application": self.format,
            }

            common.try_transfer_dicts(
                entry.get("location", {}), note_data, ["latitude", "longitude"]
            )

            tags = entry.get("tags", [])
            if entry.get("starred"):
                tags.append("day-one-starred")
            if entry.get("pinned"):
                tags.append("day-one-pinned")

            resources, note_links = self.handle_markdown_links(
                note_body, resource_id_filename_map
            )

            note_joplin = imf.Note(
                note_data,
                resources=resources,
                tags=[imf.Tag({"title": tag}) for tag in tags],
                note_links=note_links,
                original_id=entry["uuid"],
            )

            creation_date = dt.datetime.fromisoformat(entry["creationDate"])
            parent_notebook = self.create_notebook_hierarchy(creation_date)
            parent_notebook.child_notes.append(note_joplin)
