"""Convert an Email (.eml) to the intermediate format."""

import datetime
import email
import email.policy
import logging
from pathlib import Path

from jimmy import common
from jimmy import intermediate_format as imf
import jimmy.md_lib.convert


LOGGER = logging.getLogger("jimmy")


def decode_payload(part) -> str:
    content = part.get_payload(decode=True)
    charset = part.get_content_charset("utf-8")
    try:
        return content.decode(charset)
    except (LookupError, UnicodeDecodeError):
        # last resort: just decode as utf-8
        return content.decode("utf-8", errors="ignore")


def handle_part(part, attachment_folder: Path) -> tuple[list[str], imf.Resources]:
    mime = part.get_content_type()
    if mime == "text/html":
        return [jimmy.md_lib.convert.markup_to_markdown(decode_payload(part), standalone=False)], []
    if mime in ("text/markdown", "text/plain"):
        return [decode_payload(part)], []
    if any(mime.startswith(t) for t in ("audio/", "image/", "application/", "text/")):
        id_ = part.get("Content-ID")
        if id_ is not None:
            # id seems to be enclosed by <> here, but by [] in the body
            id_ = f"[cid:{id_[1:-1]}]"
        # Use the original filename if possible.
        resource_name = part.get_filename(common.unique_title())
        unique_resource_path = attachment_folder / resource_name
        content = part.get_payload(decode=True)
        unique_resource_path = common.get_unique_path(unique_resource_path, content)
        unique_resource_path.write_bytes(content)
        resource = imf.Resource(unique_resource_path, original_text=id_, title=resource_name)
        return [], [resource]
    LOGGER.debug(f"Unhandled mime type: {mime}")
    return [], []


def parse_message(message, attachment_folder: Path) -> tuple[list[str], imf.Resources]:
    body = []
    resources = []
    if message.is_multipart():
        mime = message.get_content_type()
        payloads = message.get_payload()
        if mime == "multipart/alternative":
            # choose the best payload: text is easy to process
            best_payload = message.get_body(preferencelist=("plain", "html"))
            if best_payload is not None:
                part_body, part_resources = handle_part(best_payload, attachment_folder)
                body.extend(part_body)
                resources.extend(part_resources)
            else:
                LOGGER.debug("failed to obtain body")
        else:
            # iterate over all available payloads
            for payload in payloads:
                part_body, part_resources = parse_message(payload, attachment_folder)
                body.extend(part_body)
                resources.extend(part_resources)
    else:
        part_body, part_resources = handle_part(message, attachment_folder)
        body.extend(part_body)
        resources.extend(part_resources)
    return body, resources


def eml_to_note(file_: Path, attachment_folder: Path) -> imf.Note:
    # decode the header by using the default policy
    # https://stackoverflow.com/a/55210089/7410886
    message = email.message_from_bytes(
        file_.read_bytes(),
        policy=email.policy.default,
    )

    note_imf = imf.Note(
        file_.stem,
        source_application="jimmy",
        author=str(message["From"]),
        custom_metadata={k.lower(): v for k, v in message.items()},
    )

    # parse date
    def parsedate(date_str: str | None) -> datetime.datetime | None:
        try:
            return email.utils.parsedate_to_datetime(date_str)
        except ValueError:
            return None

    if ((parsed_date := parsedate(message["Date"])) is not None) or (
        message["Received"] is not None
        and (parsed_date := parsedate(message["Received"].split("; ")[-1])) is not None
    ):
        date = parsed_date
    else:
        LOGGER.debug("failed to obtain date")
        date = None
    note_imf.created = date
    note_imf.updated = date

    body, resources = parse_message(message, attachment_folder)
    note_imf.body = "\n".join(body)
    note_imf.resources = resources

    return note_imf
