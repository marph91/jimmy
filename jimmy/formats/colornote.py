"""Convert ColorNote notes to the intermediate format."""

import hashlib
import io
import json
from pathlib import Path
import struct

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding

from jimmy import common, converter, intermediate_format as imf
import jimmy.md_lib.colornote
import jimmy.md_lib.common


class Converter(converter.BaseConverter):
    accepted_extensions = [".backup"]

    def __init__(self, config):
        super().__init__(config)
        self.password = config.password

    def parse_metadata(self, ciphertext: bytes):
        # TODO: Is the reverse-engineered data correct?
        # print(ciphertext[:8].decode("utf-8") == "NOTE")
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

    def handle_wikilink_links(self, body: str) -> imf.NoteLinks:
        # only internal links
        # https://www.colornote.com/faq-question/how-can-i-link-a-note-with-another-note/
        note_links = []
        for _, url, description in jimmy.md_lib.common.get_wikilink_links(body):
            note_links.append(imf.NoteLink(f"[[{url}]]", url, description or url))
        return note_links

    @common.catch_all_exceptions
    def convert_note(self, note_json: dict):
        # actual conversion
        # TODO: reminder, tags, ...
        title = note_json["title"]
        if title == "syncable_settings":
            # TODO: needed?
            # syncable_settings = json.loads(note_json["note"])
            # print(syncable_settings)
            return

        self.logger.debug(f'Converting note "{title}"')
        note_imf = imf.Note(
            title,
            jimmy.md_lib.colornote.colornote_to_md(note_json["note"]),
            created=common.timestamp_to_datetime(note_json["created_date"] / 1000),
            updated=common.timestamp_to_datetime(note_json["modified_date"] / 1000),
            source_application=self.format,
            original_id=title,  # not "uuid", because the title is linked
        )
        if (latitude := note_json.get("latitude", 0)) != 0:
            note_imf.latitude = latitude
        if (longitude := note_json.get("longitude", 0)) != 0:
            note_imf.longitude = longitude
        if note_json["space"] == 16:
            note_imf.tags.append(imf.Tag("colornote-archived"))
        note_imf.note_links = self.handle_wikilink_links(note_imf.body)

        self.root_notebook.child_notes.append(note_imf)

    def convert(self, file_or_folder: Path):
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

        plaintext_stream.read(first_note_index - 4)
        while chunk_length_bytes := plaintext_stream.read(4):
            # parse binary colornote format
            # 4 bytes: chunk length
            # chunk length bytes: json data
            chunk_length = struct.unpack(">L", chunk_length_bytes)[0]
            chunk_bytes = plaintext_stream.read(chunk_length)
            note_json = json.loads(chunk_bytes.decode("utf-8"))

            self.convert_note(note_json)
