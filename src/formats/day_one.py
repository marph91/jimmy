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

    def parse_rich_text(self, json_rich_text):
        # TODO: WIP
        md_content = []
        for element in json_rich_text:
            element_text = element.get("text", "")
            for attribute, value in element.get("attributes", {}).items():
                match attribute:
                    case "autolink":
                        element_text = f"<{element_text}>"
                    case "bold" | "highlightedColor":
                        element_text = f"**{element_text}**"
                    case "inlineCode":
                        element_text = f"`{element_text}`"
                    case "italic":
                        element_text = f"*{element_text}*"
                    case "line":
                        if (header := value.get("header", 0)) > 0:
                            element_text = f"{'#' * header} {element_text}*"
                        elif (list_style := value.get("listStyle")) is not None:
                            match list_style:
                                case "bulleted":
                                    bullet = "-"
                                case "numbered":
                                    bullet = "1."
                                case "checkbox":
                                    if value.get("checked"):
                                        bullet = "- [x]"
                                    else:
                                        bullet = "- [ ]"
                                case _:
                                    self.logger.warning(
                                        f"Unsupported list style {list_style}"
                                    )
                                    bullet = "-"
                            indentation = "    " * (value["indentLevel"] - 1)
                            element_text = f"{indentation}{bullet} {element_text}"
                        elif value.get("quote", False):
                            indentation = "> " * (value["indentLevel"])
                            element_text = f"{indentation}{element_text}"
                        else:
                            self.logger.warning(value, element)
                    case "linkURL":
                        if "://" in value:
                            element_text = f"[{element_text}]({value})"
                        else:
                            # assume this is a link to the dayone homepage
                            element_text = (
                                f"[{element_text}](https://dayoneapp.com"
                                f"/guides/tips-and-tutorials/{value})"
                            )
                    case _:
                        self.logger.warning(
                            f"Unsupported rich text attribute {attribute}"
                        )
            md_content.append(element_text)
        return "".join(md_content)

    def create_notebook_hierarchy(self, date_):
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
        audio_ids = []
        pdf_ids = []
        photo_id_filename_map = {}
        video_ids = []

        assert self.root_path is not None  # for mypy
        for entry in entries:
            for audio in entry.get("audios", []):
                # premium feature - not yet supported
                audio_ids.append(audio["identifier"])
            for pdf in entry.get("pdfAttachments", []):
                # premium feature - not yet supported
                pdf_ids.append(pdf["identifier"])
            for photo in entry.get("photos", []):
                potential_matches = list(
                    (self.root_path / "photos").glob(f"{photo['md5']}.*")
                )
                if len(potential_matches) == 0:
                    self.logger.warning(f"Couldn't find photo {photo['md5']}")
                elif len(potential_matches) == 1:
                    photo_id_filename_map[photo["identifier"]] = Path(
                        potential_matches[0]
                    )
                else:
                    self.logger.debug(f"Ambiguous photo {photo['md5']}")
                    photo_id_filename_map[photo["identifier"]] = Path(
                        potential_matches[0]
                    )
            for video in entry.get("videos", []):
                # premium feature - not yet supported
                video_ids.append(video["identifier"])

        if audio_ids or pdf_ids or video_ids:
            self.logger.warning(
                "Audio/PDF/Video attachments are a Day One premium feature and not "
                "yet implemented. Please provide an example file if you would like "
                "to see support."
            )

        return photo_id_filename_map

    def handle_markdown_links(
        self, body: str, photo_id_filename_map: dict
    ) -> tuple[list, list]:
        assert self.root_path is not None  # for mypy

        resources = []
        note_links = []
        for link in common.get_markdown_links(body):
            if link.is_web_link or link.is_mail_link:
                continue  # keep the original links
            if link.url.startswith("dayone2://view?entryId="):
                # internal link
                original_id = link.url.replace("dayone2://view?entryId=", "")
                note_links.append(imf.NoteLink(str(link), original_id, link.text))
            elif link.url.startswith("dayone-moment://"):
                # image
                original_id = link.url.replace("dayone-moment://", "")
                if original_id not in photo_id_filename_map:
                    self.logger.warning(f"Couldn't find resource id {original_id}")
                    continue
                source_path = (
                    self.root_path / "photos" / photo_id_filename_map[original_id]
                )
                if not source_path.is_file():
                    continue
                resources.append(imf.Resource(source_path, str(link), link.text))
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

        photo_id_filename_map = self.get_resource_maps(file_dict["entries"])

        for entry in file_dict["entries"]:
            # TODO: attach non-referenced photos, videos, audios, pdfAttachments

            note_body = entry.get("text", "")
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
                note_body, photo_id_filename_map
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
