"""Convert an Email (.eml) to the intermediate format."""

import datetime as dt
import email
import email.policy
import logging
from pathlib import Path
import time

import common
import intermediate_format as imf
import markdown_lib.common


LOGGER = logging.getLogger("jimmy")


def decode_payload(part) -> str:
    try:
        return part.get_content()
    except (LookupError, UnicodeDecodeError):
        # try to work around invalid encodings by trying with "utf-8"
        return part.get_payload(decode=True).decode("utf-8")


def handle_part(part, attachment_folder: Path) -> tuple[list[str], list[imf.Resource]]:
    mime = part.get_content_type()
    if mime == "text/html":
        return [markdown_lib.common.markup_to_markdown(decode_payload(part))], []
    if mime in ("text/markdown", "text/plain"):
        return [decode_payload(part)], []
    if any(mime.startswith(t) for t in ("audio/", "image/", "application/", "text/")):
        id_ = part.get("Content-ID")
        if id_ is not None:
            # id seems to be enclosed by <> here, but by [] in the body
            id_ = f"[cid:{id_[1:-1]}]"
        # Use the original filename if possible.
        # TODO: Files with same name are replaced.
        resource_name = part.get_filename(common.unique_title())
        unique_resource_path = attachment_folder / resource_name
        unique_resource_path.write_bytes(part.get_payload(decode=True))
        resource = imf.Resource(
            unique_resource_path, original_text=id_, title=resource_name
        )
        return [], [resource]
    LOGGER.debug(f"Unhandled mime type: {mime}")
    return [], []


def parse_message(
    message, attachment_folder: Path
) -> tuple[list[str], list[imf.Resource]]:
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
    message = email.message_from_bytes(file_.read_bytes(), policy=email.policy.default)

    # time_struct -> unix timestamp -> datetime
    if (
        message["Date"] is not None
        and (parsed_date := email.utils.parsedate(message["Date"])) is not None
    ) or (
        message["Received"] is not None
        and (parsed_date := email.utils.parsedate(message["Received"].split("; ")[-1]))
        is not None
    ):
        date = dt.datetime.fromtimestamp(int(time.mktime(parsed_date)))
    else:
        LOGGER.debug("failed to obtain date")
        date = None

    body, resources = parse_message(message, attachment_folder)

    note_imf = imf.Note(
        # TODO: f"{0 if date is None else date.isoformat()}_{message["Subject"]}",
        file_.stem,
        "\n".join([f"# {message["Subject"]}", ""] + body),
        source_application="jimmy",
        resources=resources,
        created=date,
        updated=date,
        author=message["From"],
    )
    return note_imf
