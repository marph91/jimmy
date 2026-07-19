"""Convert ColorNote notes to the intermediate format."""

import hashlib
import io
import json
from pathlib import Path
import struct

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from src.jimmy import common, converter, intermediate_format as imf
import src.jimmy.md_lib.colornote
import src.jimmy.md_lib.links


class Converter(converter.BaseConverter):
    def __init__(self, config: common.Config):
        super().__init__(config)
        self.password = config.password
        self.calendar_notebook = imf.Notebook("Calendar")
        self.archive_notebook = imf.Notebook("Archive")
        self.trash_notebook = imf.Notebook("Trash")

    def parse_metadata(self, ciphertext: bytes):
        # TODO: Is the reverse-engineered data correct?
        # TODO: Why utf-16 is needed here? Else "NOTE" is decoded, but it has a length of 8.
        # TODO: Could be also "一伀吀䔀", so better skip this check.
        # if (keyword := ciphertext[:8].decode("utf-16")) != "NOTE":
        #     self.logger.debug(f'Expected keyword "NOTE", got "{keyword}".')
        major, minor, timestamp, note_count = struct.unpack(">LLQL", ciphertext[8:])
        date = common.timestamp_to_datetime(timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")
        self.logger.info(
            f"Metadata: {note_count} notes exported at {date} with version {major}.{minor}"
        )

    def decrypt(self, salt: bytes, password: bytes, ciphertext: bytes) -> bytes | None:
        # decrypting is based on:
        # https://github.com/olejorgenb/ColorNote-backup-decryptor/blob/61e105d6f13b2cd22b5141b6334bb098617665e1/src/ColorNoteBackupDecrypt.java
        key = hashlib.md5(password + salt).digest()
        iv = hashlib.md5(key + password + salt).digest()

        cipher = Cipher(algorithms.AES128(key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        plaintext_padded = decryptor.update(ciphertext) + decryptor.finalize()

        unpadder = padding.PKCS7(cipher.algorithm.block_size).unpadder()
        try:
            plaintext = unpadder.update(plaintext_padded) + unpadder.finalize()
            return plaintext
        except ValueError as exc:
            self.logger.error("Decrypting failed. Wrong password?")
            self.logger.debug(exc, exc_info=True)
            return None

    def handle_links(self, body: str) -> imf.NoteLinks:
        # only internal links
        # https://www.colornote.com/faq-question/how-can-i-link-a-note-with-another-note/
        note_links = []
        for link in src.jimmy.md_lib.links.get_markdown_links(body):
            note_links.append(imf.NoteLink(str(link), link.url, link.text or link.url))
        return note_links

    @common.catch_all_exceptions
    def convert_note(self, note_json: dict):
        # actual conversion
        # TODO: reminder, tags, ...
        title = note_json["title"]
        if title in ("name_master_password", "syncable_settings"):
            self.logger.debug(f'Skipping note "{title}"')
            # TODO: needed?
            # syncable_settings = json.loads(note_json["note"])
            # print(syncable_settings)
            return

        if title == "" and note_json.get("note", "") == "":
            self.logger.debug("Skipping empty note")
            # Not sure why they exist. Couldn't find anything special in metadata.
            return

        if note_json["folder_id"] == 16:  # calendar notes should have the date as title
            base_date = common.timestamp_to_datetime(note_json["reminder_base"] / 1000)
            title = base_date.strftime("%Y-%m-%d")

        self.logger.debug(f'Converting note "{title}"')
        note_imf = imf.Note(
            title,
            src.jimmy.md_lib.colornote.colornote_to_md(note_json["note"]),
            created=common.timestamp_to_datetime(note_json["created_date"] / 1000),
            updated=common.timestamp_to_datetime(note_json["modified_date"] / 1000),
            source_application=self.format,
            original_id=title,  # not "uuid", because the title is linked
            custom_metadata={"color_index": note_json["color_index"]},
        )
        if (latitude := note_json.get("latitude", 0)) != 0:
            note_imf.latitude = latitude
        if (longitude := note_json.get("longitude", 0)) != 0:
            note_imf.longitude = longitude
        note_imf.note_links = self.handle_links(note_imf.body)

        # determine parent notebook (root, calendar, archive or trash)
        parent_notebook = self.root_notebook
        match note_json["folder_id"]:
            case 0:
                pass
            case 16:  # calendar
                parent_notebook = self.calendar_notebook
            case _:
                self.logger.debug(f"Unexpected folder_id: {note_json['folder_id']}")
        match note_json["active_state"]:
            case 0:
                pass
            case 16:  # trash
                parent_notebook = self.trash_notebook
            case _:
                self.logger.debug(f"Unexpected active_state: {note_json['active_state']}")
        match note_json["space"]:
            case 0:
                pass
            case 16:  # archive
                parent_notebook = self.archive_notebook
            case _:
                self.logger.debug(f"Unexpected space: {note_json['space']}")
        parent_notebook.child_notes.append(note_imf)

    def convert(self, file_or_folder: Path):
        if self.password is None:
            self.password = "0000"
            self.logger.warning("No password given. Trying with default password '0000'.")

        ciphertext = file_or_folder.read_bytes()

        self.parse_metadata(ciphertext[:28])
        plaintext = self.decrypt(
            b"ColorNote Fixed Salt", self.password.encode("utf-8"), ciphertext[28:]
        )
        if plaintext is None:
            return

        plaintext_stream = io.BytesIO(plaintext)

        # search for '{"_id":'
        # TODO: Meaning of the bytes before? Looks similar to the iv.
        first_note_index = plaintext.find(bytearray.fromhex("7b225f6964223a"))
        if first_note_index == -1:
            self.logger.error("Couldn't find start position of the first note.")
            return

        self.root_notebook.child_notebooks.extend(
            [self.calendar_notebook, self.archive_notebook, self.trash_notebook]
        )

        plaintext_stream.read(first_note_index - 4)
        while chunk_length_bytes := plaintext_stream.read(4):
            # parse binary colornote format
            # 4 bytes: chunk length
            # chunk length bytes: json data
            chunk_length = struct.unpack(">L", chunk_length_bytes)[0]
            chunk_bytes = plaintext_stream.read(chunk_length)
            note_json = json.loads(chunk_bytes.decode("utf-8"))

            self.convert_note(note_json)

        self.remove_empty_notebooks()
