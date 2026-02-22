"""Convert Reflect notes to the intermediate format."""

import json
from pathlib import Path

from jimmy import common, converter, intermediate_format as imf
import jimmy.md_lib.links
import jimmy.md_lib.text


class Converter(converter.BaseConverter):
    def reflect_json_to_markdown(
        self,
        note_json: dict,
        note_md: list[str] | None = None,
        tags: imf.Tags | None = None,
        note_links: imf.NoteLinks | None = None,
    ) -> tuple[list[str], imf.Tags, imf.NoteLinks]:
        if note_md is None:
            note_md = []
        if tags is None:
            tags = []
        if note_links is None:
            note_links = []
        match note_json["type"]:
            case "backlink":
                backlink_md = jimmy.md_lib.links.make_link(
                    note_json["attrs"]["label"], note_json["attrs"]["id"]
                )
                note_md.append(backlink_md)
                note_links.append(
                    imf.NoteLink(backlink_md, note_json["attrs"]["id"], note_json["attrs"]["label"])
                )
            case "codeBlock":
                language = note_json["attrs"].get("language", "")
                note_md.append(f"\n\n```{language}\n")
            case "doc":
                pass  # toplevel type
            case "hardBreak" | "paragraph":
                # somehow paragraphs are added directly after lists
                if note_md[-1] in ["- ", "1. ", "- [ ] ", "- [x] "]:
                    note_md.insert(-1, "\n\n")
                else:
                    note_md.append("\n\n")
            case "heading":
                if (level := note_json["attrs"]["level"]) > 1:
                    note_md.append("\n\n")
                note_md.append("#" * level + " ")
            case "file":
                # print(note_json)
                note_md.append(
                    jimmy.md_lib.links.make_link(
                        note_json["attrs"]["fileName"], note_json["attrs"]["url"]
                    )
                )
            case "image":
                # print(note_json)
                note_md.append(
                    jimmy.md_lib.links.make_link(
                        note_json["attrs"]["alt"],
                        note_json["attrs"]["src"],
                        is_image=True,
                        title=note_json["attrs"]["title"],
                    )
                )
            case "list":
                match note_json["attrs"]["kind"]:
                    case "bullet":
                        note_md.append("- ")
                    case "checklist":
                        if note_json["attrs"]["checked"]:
                            note_md.append("- [x] ")
                        else:
                            note_md.append("- [ ] ")
                    case "ordered":
                        note_md.append("1. ")
                    case _:
                        self.logger.warning(f"Unsupported list type: {note_json['attrs']['kind']}")
            case "tag":
                label = note_json["attrs"]["label"]
                note_md.append(f"#{label}")
                tags.append(imf.Tag(label, original_id=note_json["attrs"]["id"]))
            case "text":
                leading_whitespace, text_md, trailing_whitespace = (
                    jimmy.md_lib.text.split_leading_trailing_whitespace(note_json["text"])
                )
                # TODO: split leading and trailing whitespace
                link = None
                for mark in note_json.get("marks", []):
                    match mark["type"]:
                        case "bold":
                            text_md = f"**{text_md}**"
                        case "code":
                            text_md = f"`{text_md}`"
                        case "italic":
                            text_md = f"*{text_md}*"
                        case "link":
                            link = mark  # handled later
                        case "strike":
                            text_md = f"~~{text_md}~~"
                        case "textHighlight":
                            text_md = f"=={text_md}=="
                        case "underline":
                            text_md = f"++{text_md}++"
                        case _:
                            self.logger.warning(f"Unsupported markup: {mark['type']}")
                # handle links last to apply other markup correctly
                if link is not None:
                    text_md = jimmy.md_lib.links.make_link(text_md, link["attrs"]["href"])
                note_md.append(leading_whitespace + text_md + trailing_whitespace)
            case _:
                self.logger.warning(f"Unsupported type: {note_json['type']}")

        for json_content in note_json.get("content", []):
            note_md, tags, note_links = self.reflect_json_to_markdown(
                json_content,
                note_md=note_md,
                tags=tags,
                note_links=note_links,
            )
        # print(json.dumps(note_json, indent=2))
        if note_json["type"] == "codeBlock":
            # add closing brackets
            note_md.append("\n```\n")
        return note_md, tags, note_links

    @common.catch_all_exceptions
    def convert_note(self, note_json: dict):
        title = note_json["subject"]
        self.logger.debug(f'Converting note "{title}"')
        note_imf = imf.Note(
            title,
            created=common.iso_to_datetime(note_json["created_at"]),
            updated=common.iso_to_datetime(note_json["updated_at"]),
            source_application=self.format,
            original_id=note_json["id"],
        )
        body_list, note_imf.tags, note_imf.note_links = self.reflect_json_to_markdown(
            json.loads(note_json["document_json"])
        )
        note_imf.body = "".join(body_list)
        self.root_notebook.child_notes.append(note_imf)

    def convert(self, file_or_folder: Path):
        input_json = json.loads(file_or_folder.read_text(encoding="utf-8"))
        if "notes" not in input_json:
            self.logger.error('"notes" not found. Is this really a clipto export?')
            return

        if (export_version := input_json.get("export_version")) != "1.0":
            self.logger.warning(f"Unsupported export version {export_version}")
        if (graph_version := input_json.get("graph_version")) != 15:
            self.logger.warning(f"Unsupported graph version {graph_version}")

        for note in input_json.get("notes", []):
            self.convert_note(note)
