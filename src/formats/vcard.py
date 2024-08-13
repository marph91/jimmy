"""Convert vCard contacts to the intermediate format."""

from pathlib import Path
import vobject

import converter
import intermediate_format as imf


def vcard_list_to_markdown(name: str, list_: list) -> list[str]:
    # remove duplicates (set can't be used, because there are unhashable items)
    # TODO: check if there is a more elegant way
    unique_list = []
    for item in list_:
        if item.value not in unique_list:
            unique_list.append(item.value)
    if len(unique_list) == 1:
        normalized_value = str(list_[0].value).replace("\n", " ")
        return [f"- {name}: {normalized_value}"]
    markdown = [f"- {name}:"]
    for item in unique_list:
        normalized_value = str(item).replace("\n", " ")
        markdown.append(f"    - {normalized_value}")
    return markdown


class Converter(converter.BaseConverter):
    accepted_extensions = [".vcf"]

    def convert(self, file_or_folder: Path):
        for contact in vobject.readComponents(
            file_or_folder.read_text(encoding="utf-8")
        ):
            body = []

            for key, value in contact.contents.items():
                match key:
                    case (
                        "fn"
                        | "n"
                        | "prodid"
                        | "rev"
                        | "uid"
                        | "version"
                        | "x-ablabel"
                    ):
                        pass  # handled separately or ignored on purpose
                    case "adr":
                        # TODO: trailing commata
                        body.extend(vcard_list_to_markdown("Address", value))
                    case "bday":
                        body.extend(vcard_list_to_markdown("Birthday", value))
                    case "email":
                        body.extend(vcard_list_to_markdown("Email", value))
                    case "nickname":
                        body.extend(vcard_list_to_markdown("Nickname", value))
                    case "note":
                        body.extend(vcard_list_to_markdown("Note", value))
                    case "org":
                        # RFC 2426: 3.5.5 ORG Type Definition
                        # The org type is a list with:
                        # - organizational name
                        # - organizational unit #1 name
                        # - organizational unit #2 name
                        # Take the organizational name only for now.
                        name = "Organisations"
                        if len(value) == 1:
                            body.append(f"- {name}: {value[0].value[0]}")
                        else:
                            body.append(f"- {name}:")
                            for organization in value:
                                body.append(f"    - {organization.value[0]}")
                    case "tel":
                        # TODO: sometimes there are duplicated numbers
                        body.extend(vcard_list_to_markdown("Telephone", value))
                    case "x-android-custom" | "x-mozilla-custom1":
                        body.extend(vcard_list_to_markdown("Custom Information", value))
                    case _:
                        self.logger.debug(f"ignoring unsupported {key}: {value}")
            note_joplin = imf.Note(
                {
                    "title": contact.fn.value,
                    "body": "\n".join(body),
                    "source_application": self.format,
                }
            )
            self.root_notebook.child_notes.append(note_joplin)
