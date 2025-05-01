"""Convert Day One notes to the intermediate format."""

from pathlib import Path
import json

from jimmy import common, converter, intermediate_format as imf
import jimmy.md_lib.common


class Converter(converter.BaseConverter):
    accepted_extensions = [".zip"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.note_names_per_journal = []

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

        for link in jimmy.md_lib.common.get_markdown_links(body):
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

    def get_unique_name(self, name: str) -> str:
        """Find a unique name for a note."""
        # Prevent linking issues if the note is renamed later.
        # TODO: similar to common.get_unique_name
        if name not in self.note_names_per_journal:
            return name

        found_new_name = False
        for new_index in range(1, 10000):
            new_name = f"{name}-{new_index:04}"
            if new_name not in self.note_names_per_journal:
                found_new_name = True
                break
        if not found_new_name:
            # last resort
            new_name = f"{name}-{common.uuid_title()}"

        self.logger.debug(f'Note "{name}" exists already. New name: "{new_name}".')
        return new_name

    @common.catch_all_exceptions
    def convert_note(
        self, entry, resource_id_filename_map, root_notebook: imf.Notebook
    ):
        created = common.iso_to_datetime(entry["creationDate"])
        title = self.get_unique_name(created.strftime("%Y-%m-%d"))
        self.note_names_per_journal.append(title)
        self.logger.debug(f'Converting note "{title}"')

        note_imf = imf.Note(
            title,
            created=created,
            updated=common.iso_to_datetime(entry["modifiedDate"]),
            source_application=self.format,
            original_id=entry["uuid"],
        )

        note_imf.body = entry.get(
            "text", ""
        )  # TODO: Is there any advantage of rich text?
        # Backslashes are added often. Removing them like this might cause issues.
        note_imf.body = note_imf.body.replace("\\", "")
        # https://stackoverflow.com/a/55400921/7410886
        note_imf.body = note_imf.body.replace("\u200b", "")

        note_imf.tags.extend([imf.Tag(tag) for tag in entry.get("tags", [])])
        if entry.get("starred"):
            note_imf.tags.append(imf.Tag("day-one-starred"))
        if entry.get("pinned"):
            note_imf.tags.append(imf.Tag("day-one-pinned"))

        note_imf.resources, note_imf.note_links = self.handle_markdown_links(
            note_imf.body, resource_id_filename_map
        )

        if (location := entry.get("location")) is not None:
            note_imf.latitude = location["latitude"]
            note_imf.longitude = location["longitude"]

        root_notebook.child_notes.append(note_imf)

    def convert(self, file_or_folder: Path):
        journals = list(self.root_path.glob("*.json"))
        if len(journals) == 0:
            self.logger.warning(
                "Couldn't find json file in the zip. Is this really a Day One export?"
            )
            return

        for journal in journals:
            root_notebook = imf.Notebook(journal.stem)
            self.root_notebook.child_notebooks.append(root_notebook)

            self.note_names_per_journal = []
            input_json = json.loads(journal.read_text(encoding="utf-8"))
            resource_id_filename_map = self.get_resource_maps(input_json["entries"])
            for entry in input_json["entries"]:
                # TODO: attach non-referenced photos, videos, audios, pdfAttachments?
                self.convert_note(entry, resource_id_filename_map, root_notebook)
