"""Convert ColorNote notes to the intermediate format."""

import hashlib
import io
import json
from pathlib import Path
import struct

from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import unpad

import common
import converter
import intermediate_format as imf
import markdown_lib.colornote
import markdown_lib.common


def decrypt(salt: bytes, password: bytes, ciphertext: bytes) -> bytes:
    # decrypting is based on:
    # https://github.com/olejorgenb/ColorNote-backup-decryptor/blob/61e105d6f13b2cd22b5141b6334bb098617665e1/src/ColorNoteBackupDecrypt.java
    key = hashlib.md5(password + salt).digest()
    iv = hashlib.md5(key + password + salt).digest()
    decoder = AES.new(key, AES.MODE_CBC, iv)
    return unpad(decoder.decrypt(ciphertext), 16)


class Converter(converter.BaseConverter):
    accepted_extensions = [".backup"]

    def __init__(self, config):
        super().__init__(config)
        self.password = config.password

    def handle_wikilink_links(self, body: str) -> list[imf.NoteLink]:
        # only internal links
        # https://www.colornote.com/faq-question/how-can-i-link-a-note-with-another-note/
        note_links = []
        for _, url, description in markdown_lib.common.get_wikilink_links(body):
            note_links.append(imf.NoteLink(f"[[{url}]]", url, description or url))
        return note_links

    def convert(self, file_or_folder: Path):
        ciphertext = file_or_folder.read_bytes()
        # TODO: Meaning of ciphertext[:28]?
        plaintext = decrypt(
            b"ColorNote Fixed Salt", self.password.encode("utf-8"), ciphertext[28:]
        )

        # TODO: Meaning of plaintext[:16]? Looks similar to the iv.
        plaintext_stream = io.BytesIO(plaintext)
        plaintext_stream.read(16)
        while chunk_length_bytes := plaintext_stream.read(4):
            # parse binary colornote format
            # 4 bytes: chunk length
            # chunk length bytes: json data
            (chunk_length,) = struct.unpack(">L", chunk_length_bytes)
            chunk_bytes = plaintext_stream.read(chunk_length)
            note_json = json.loads(chunk_bytes.decode("utf-8"))

            # actual conversion
            # TODO: reminder, tags, ...
            title = note_json["title"]
            if title == "syncable_settings":
                # TODO: needed?
                # syncable_settings = json.loads(note_json["note"])
                # print(syncable_settings)
                continue
            self.logger.debug(f'Converting note "{title}"')
            note_imf = imf.Note(
                title,
                markdown_lib.colornote.colornote_to_md(note_json["note"]),
                created=common.timestamp_to_datetime(note_json["created_date"] / 1000),
                updated=common.timestamp_to_datetime(note_json["modified_date"] / 1000),
                source_application=self.format,
                original_id=title,  # not "uuid", because the title is linked
                latitude=note_json["latitude"],
                longitude=note_json["longitude"],
            )
            if note_json["space"] == 16:
                note_imf.tags.append(imf.Tag("colornote-archived"))
            note_imf.note_links = self.handle_wikilink_links(note_imf.body)

            self.root_notebook.child_notes.append(note_imf)
