"""Convert a Diaro backup to the intermediate format."""

from collections import defaultdict
from pathlib import Path
import xml.etree.ElementTree as ET  # noqa: N817

from jimmy import common, converter, intermediate_format as imf


# TODO: move to common
def get_text(element, default: str | None = None) -> str | None:
    if element is not None and element.text is not None:
        return element.text
    return default


class Converter(converter.BaseConverter):
    accepted_extensions = [".zip"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attachments = defaultdict(list)
        self.locations = {}
        self.moods = {}
        self.tags = {}

    def parse_metadata(self, root_node):
        for table in root_node.findall("table"):
            table_name = table.attrib.get("name")
            if table_name in ("diaro_entries", "diaro_folders", "diaro_templates"):
                continue  # handle notes and notebooks later, ignore templates for now
            for item in table:
                match table_name:
                    case "diaro_attachments":
                        # entry_uid is the ID of the target note.
                        # uid seems to be not needed.
                        if not (filename := get_text(item.find("filename"))):
                            self.logger.debug("Empty filename. Ignore ressource.")
                            continue
                        if not (type_ := get_text(item.find("type"))):
                            self.logger.debug("Empty type. Ignore ressource.")
                            continue
                        self.attachments[get_text(item.find("entry_uid"))].append(
                            imf.Resource(self.root_path / "media" / type_ / filename)
                        )
                    case "diaro_locations":
                        if (latitude := get_text(item.find("lat"))) and (
                            longitude := get_text(item.find("lng"))
                        ):
                            self.locations[get_text(item.find("uid"))] = {
                                "latitude": latitude,
                                "longitude": longitude,
                            }
                    case "diaro_moods":
                        self.moods[get_text(item.find("uid"))] = get_text(
                            item.find("title")
                        )
                    case "diaro_tags":
                        self.tags[get_text(item.find("uid"))] = get_text(
                            item.find("title")
                        )
                    case _:
                        self.logger.debug(f'Ignoring table "{table_name}"')

    @common.catch_all_exceptions
    def convert_notebook(self, folder):
        # there seems to be only one level of folders
        notebook = imf.Notebook(
            get_text(folder.find("title")) or common.unique_title(),
            original_id=get_text(folder.find("uid")),
        )
        self.root_notebook.child_notebooks.append(notebook)

    @common.catch_all_exceptions
    def convert_note(self, entry):
        # date is UTC - tz-offset can be ignored
        timestamp = get_text(entry.find("date"))
        assert timestamp is not None
        date_ = common.timestamp_to_datetime(int(timestamp) // 10**3)
        title = f"{date_.strftime('%Y-%m-%d')} {get_text(entry.find('title'), '')}"
        self.logger.debug(f'Converting note "{title}"')
        note_imf = imf.Note(
            title,
            get_text(entry.find("text")) or "",
            original_id=get_text(entry.find("uid")),
            created=date_,
            updated=date_,
        )

        # TODO: weather, mood

        # location
        if location_data := self.locations.get(get_text(entry.find("location_uid"))):
            note_imf.latitude = location_data["latitude"]
            note_imf.longitude = location_data["longitude"]

        # tags
        if (tags := get_text(entry.find("tags"))) is not None:
            for diaro_tag in tags.split(","):
                if diaro_tag.strip():
                    note_imf.tags.append(imf.Tag(diaro_tag.strip()))

        # ressources
        note_imf.resources = self.attachments.get(note_imf.original_id, [])

        # folder
        parent_folder_uid = get_text(entry.find("folder_uid"))
        parent_notebook = self.root_notebook  # fallback
        for potential_parent in self.root_notebook.child_notebooks:
            if potential_parent.original_id == parent_folder_uid:
                parent_notebook = potential_parent
                break
        parent_notebook.child_notes.append(note_imf)

    def convert(self, file_or_folder: Path):
        target_file = self.root_path / "DiaroBackup.xml"
        if not target_file.is_file():
            self.logger.error(
                'Could not find "DiaroBackup.xml" file in zip. '
                "Is this really a Diaro backup?"
            )
            return
        root_node = ET.parse(target_file).getroot()
        if int(version := root_node.attrib.get("version", "0")) != 2:
            self.logger.warning(f"Unsupported version: {version}")

        self.parse_metadata(root_node)

        folders = root_node.find("./table[@name='diaro_folders']")
        if folders is not None:
            for folder in folders:
                self.convert_notebook(folder)

        entries = root_node.find("./table[@name='diaro_entries']")
        if entries is not None:
            for entry in entries:
                self.convert_note(entry)

        # Don't export empty notebooks
        self.remove_empty_notebooks()
