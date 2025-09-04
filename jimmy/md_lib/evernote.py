"""Convert the enex (xml) note content to Markdown."""

import base64
import copy
import hashlib
import hmac
import logging
import xml.etree.ElementTree as ET  # noqa: N817

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding

import jimmy.md_lib.common


LOGGER = logging.getLogger("jimmy")


def decrypt(base64_data: str, password: bytes) -> str | None:
    if not password:
        LOGGER.warning('Could not decrypt. Set the password by "--password"')
        return None

    # Extract the encoded data.
    binary_data = base64.b64decode(base64_data)
    # assert binary_data[0:4] == b"ENC0"
    salt = binary_data[4:20]
    hmac_salt = binary_data[20:36]
    iv = binary_data[36:52]
    ciphertext = binary_data[52:-32]
    hmac_message = binary_data[:-32]
    hmac_reference_digest = binary_data[-32:]

    # Check if the HMAC is valid.
    hmac_key = hashlib.pbkdf2_hmac("SHA256", password, hmac_salt, 50000, 16)
    hmac_digest = hmac.new(hmac_key, hmac_message, hashlib.sha256)
    hmac_valid = hmac.compare_digest(hmac_digest.digest(), hmac_reference_digest)

    if not hmac_valid:
        LOGGER.warning("Could not decrypt test data. Incorrect password?")
        return None

    key = hashlib.pbkdf2_hmac("SHA256", password, salt, 50000, 16)
    cipher = Cipher(algorithms.AES128(key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    plaintext_padded = decryptor.update(ciphertext) + decryptor.finalize()
    unpadder = padding.PKCS7(cipher.algorithm.block_size).unpadder()
    plaintext = unpadder.update(plaintext_padded) + unpadder.finalize()
    return plaintext.decode("utf-8")


class EnexToMarkdown:
    """https://docs.python.org/3/library/xml.etree.elementtree.html#xmlparser-objects"""

    def __init__(self, password: str):
        self.password = password

        self.global_level = 0
        self.active_lists: list[str] = []
        self.active_formatting: dict[str, int] = {}
        self.active_link: dict = {}
        self.active_resource: dict[str, str] = {}
        self.encryption: dict | None = None
        self.in_table = False
        self.table_row: list[str] = []
        self.table_cell: list[str] = []
        self.current_table = jimmy.md_lib.common.MarkdownTable()
        self.quote_level = 0
        self.newlines_after_formatting = 0
        self.hashes: list[str] = []
        self.md: list[str] = []

    def add_newlines(self, count: int):
        """Add as many newlines as needed. Consider preceding newlines."""
        # TODO: check for simpler implementation
        if not self.md:
            return
        # how many newlines are at the end already?
        index = 0
        while index < len(self.md) and index < count and self.md[-index - 1] == "\n":
            index += 1
        # insert missing newlines
        if index > 0:
            self.md[-index:] = ["\n"] * count
        else:
            self.md.extend(["\n"] * count)

    def start(self, tag: str, attrib: dict):
        self.global_level += 1

        match tag:
            case "a":
                # link
                self.active_link["href"] = attrib.get("href")
                for title_tag in ["title", "name", "alt"]:
                    if (title := attrib.get(title_tag)) is not None:
                        self.active_link["alt"] = title
                        break
            case "b" | "strong":
                if "bold" in self.active_formatting:
                    return
                self.md.append("**")
                self.active_formatting["bold"] = self.global_level
            case "br":
                self.add_newlines(1)
            case "blockquote":
                self.quote_level += 1
            case "center" | "div" | "font" | "en-note" | "span":
                pass  # only interested in attributes and data
            case "code":
                if "code" in self.active_formatting:
                    return
                self.md.append("`")
                self.active_formatting["code"] = self.global_level
            case "en-crypt":
                self.encryption = {
                    "cipher": attrib.get("cipher"),
                    "hint": attrib.get("hint"),
                    "length": attrib.get("length"),
                }
            case "en-media":
                # inline resource (base64 encoded)
                self.active_resource = {"hash": attrib["hash"]}
            case "h1" | "h2" | "h3" | "h4" | "h5" | "h6" | "h7":
                heading_md = "#" * int(tag[-1]) + " "
                if self.active_link:
                    self.active_link["prepend"] = [heading_md]
                    self.active_link["append"] = ["\n"] * 2
                else:
                    self.add_newlines(2)  # ensure empty line
                    self.md.append(heading_md)
            case "hr":
                self.add_newlines(2)  # ensure empty line
                self.md.append("---")
                self.add_newlines(2)  # ensure empty line
            case "em" | "i" | "cite":
                # TODO: cite == italic?
                if "italic" in self.active_formatting:
                    return
                self.md.append("*")
                self.active_formatting["italic"] = self.global_level
            case "img":
                if (url := attrib.get("src")) is not None:
                    self.md.append(f"![{attrib.get('title', attrib.get('alt', ''))}]({url})")
            case "p":
                self.add_newlines(2)
            case "s":
                if "strikethrough" in self.active_formatting:
                    return
                self.md.append("~~")
                self.active_formatting["strikethrough"] = self.global_level
            case "u":
                if "underline" in self.active_formatting:
                    return
                self.md.append("++")
                self.active_formatting["underline"] = self.global_level
            # table
            case "table":
                self.add_newlines(2)  # ensure empty line
                self.in_table = True
            case "col" | "colgroup" | "tbody" | "td" | "th" | "thead" | "tr":
                pass  # we handle them at closing tag
            # list
            case "en-todo":
                if self.active_lists and self.active_lists[-1] == "ul":
                    # in a <li>
                    bullet = "[x] " if attrib.get("checked") in [True, "true"] else "[ ] "
                else:
                    # in a <div>
                    # TODO: integrate in active_lists
                    self.add_newlines(2)  # ensure empty line
                    bullet = "- [x] " if attrib.get("checked") in [True, "true"] else "- [ ] "
                self.md.append(bullet)
            case "ol" | "ul":
                self.add_newlines(2)  # ensure empty line
                self.active_lists.append(tag)
            case "li":
                if "--en-checked:true" in attrib.get("style", ""):
                    bullet = "- [x] "
                elif "--en-checked:false" in attrib.get("style", ""):
                    bullet = "- [ ] "
                else:
                    bullet = {"ol": "1. ", "ul": "- "}[self.active_lists[-1]]
                self.md.append(" " * 4 * (len(self.active_lists) - 1) + bullet)
            case _:
                LOGGER.debug(f"ignoring opening tag {tag}")

        for key, value in attrib.items():
            match key:
                case "style":
                    # TODO: other styles
                    style_items = [v.strip() for v in value.split(";") if v.strip()]
                    for item in style_items:
                        try:
                            style, value = item.split(":", maxsplit=1)
                            style = style.strip()
                            value = value.strip()
                        except ValueError:
                            continue

                        match style:
                            case "-en-codeblock" | "--en-codeblock":
                                if value == "true":
                                    self.add_newlines(2)  # ensure empty line
                                    self.md.append("```")
                                    self.add_newlines(1)
                                    self.active_formatting["codeblock"] = self.global_level
                            case "-evernote-highlight":
                                if value == "true" and "bold" not in self.active_formatting:
                                    # highlight is converted to bold
                                    self.md.append("**")
                                    self.active_formatting["bold"] = self.global_level
                            case "--en-id":
                                # will be replaced with tasks later
                                self.md.append(f"tasklist://{value}")
                            # case "--en-todo":
                            #     if value == "true":
                            #         self.active_lists.append("tasklist")
                            case "font-family":
                                if value == "monospace" and "code" not in self.active_formatting:
                                    self.md.append("`")
                                    self.active_formatting["code"] = self.global_level
                            case "font-style":
                                # https://developer.mozilla.org/en-US/docs/Web/CSS/font-style
                                if value == "italic" and "italic" not in self.active_formatting:
                                    self.md.append("*")
                                    self.active_formatting["italic"] = self.global_level
                                # TODO: handle value == "normal"?
                            case "font-weight":
                                if (
                                    value in ["bold", "bolder"]
                                    or value.isdigit()
                                    and int(value) >= 700
                                ) and "bold" not in self.active_formatting:
                                    # https://www.w3schools.com/cssref/pr_font_weight.php
                                    # 700 and above is bold
                                    self.md.append("**")
                                    self.active_formatting["bold"] = self.global_level
                                elif value == "italic" and "italic" not in self.active_formatting:
                                    self.md.append("*")
                                    self.active_formatting["italic"] = self.global_level
                            # TODO: padding-left:40px;
                            # case "padding-left":
                            #     pass
                            # for debugging only
                            # case _:
                            #     print(style, value)
                case "size":
                    # https://www.geeksforgeeks.org/html-font-size-attribute/
                    # default: 3 - make everything above bold
                    if "bold" in self.active_formatting or int(value) <= 3:
                        continue
                    self.md.append("**")
                    self.active_formatting["bold"] = self.global_level
                case "start":
                    pass  # TODO: start of ordered/numbered list
                case (
                    "align"
                    | "alt"
                    | "border"
                    | "checked"
                    | "cipher"
                    | "clear"
                    | "color"
                    | "dir"
                    | "face"
                    | "hash"
                    | "height"
                    | "hint"
                    | "href"
                    | "lang"
                    | "length"
                    | "name"
                    | "rel"
                    | "rev"
                    | "shape"
                    | "src"
                    | "target"
                    | "title"
                    | "type"
                    | "width"
                ):
                    pass  # handled later or ignored
                case _:
                    LOGGER.debug(f'tag "{tag}", ignoring attribute "{key}: {value}"')

    def end(self, tag: str):
        newlines = 0
        match tag:
            case "a":
                # internal note link
                if self.active_link:
                    if prepend := self.active_link.get("prepend"):
                        self.md.extend(prepend)
                    title = self.active_link.get("title", self.active_link.get("alt"))
                    url = self.active_link["href"]
                    if url is None or url.strip() == "#":
                        url = None
                    if title is None and url is None:
                        pass
                    elif title == url or title is None:
                        # normal link
                        self.md.append(f"<{url}>")
                    elif url is None:
                        # no URL to link
                        self.md.append(title)
                    # elif url.startswith("data:image/"):
                    #     # data:image/ resources seem to be duplicated
                    #     # TODO: Is this always the case?
                    #     pass
                    else:
                        # normal link
                        self.md.append(f"[{title}]({url})")
                    if append := self.active_link.get("append"):
                        self.md.extend(append)
                    self.active_link = {}
            case "b" | "i" | "s" | "u" | "center" | "cite" | "code" | "em" | "font" | "strong":
                pass  # handled already in active_formatting, TODO: sanity check
            case "br" | "div":
                newlines = 1
            case "blockquote":
                self.quote_level -= 1
            case "en-crypt":
                self.encryption = None
            case "en-media":
                title = self.active_resource.get("title", self.active_link.get("alt", ""))
                self.md.append(f"![{title}]({self.active_resource['hash']})")
                self.hashes.append(self.active_resource["hash"])
                self.active_resource = {}

                # clear active link (if there is any) to don't duplicate
                self.active_link = {}
            case "en-note" | "span":
                pass
            case "h1" | "h2" | "h3" | "h4" | "h5" | "h6" | "h7":
                newlines = 2
            case "hr":
                newlines = 2
            case "img":
                newlines = 1
            case "p":
                self.add_newlines(2)
            # table
            case "table":
                self.md.append(self.current_table.create_md())
                # ensure empty line (there is already one newline added at "create_md")
                newlines = 1
                self.in_table = False
                self.current_table = jimmy.md_lib.common.MarkdownTable()
            case "colgroup" | "th":
                # header row finished
                self.current_table.header_rows.append(self.table_row)
                self.table_row = []
            case "tr":
                # data row finished
                self.current_table.data_rows.append(self.table_row)
                self.table_row = []
            case "col" | "td" | "th":
                self.table_row.append("".join(self.table_cell))
                self.table_cell = []
            case "tbody" | "thead":
                pass
            # list
            case "en-todo":
                pass
            case "ol" | "ul":
                newlines = 2  # ensure empty line
                list_type = self.active_lists.pop()
                if list_type != tag:
                    LOGGER.debug(f"Expected list '{list_type}', actual '{tag}'")
            case "li":
                pass
            case _:
                LOGGER.debug(f"ignoring closing tag {tag}")

        self.global_level -= 1

        active_formatting = copy.deepcopy(self.active_formatting)
        for formatting, stop_level in active_formatting.items():
            if self.global_level >= stop_level:
                continue
            match formatting:
                case "bold":
                    self.md.append("**")
                case "code":
                    self.md.append("`")
                case "codeblock":
                    self.md.append("```")
                    newlines = 2  # ensure empty line
                case "italic":
                    self.md.append("*")
                case "strikethrough":
                    self.md.append("~~")
                case "underline":
                    self.md.append("++")
                case _:
                    LOGGER.debug(f'unhandled formatting "{formatting}"')
            if self.md[-2] == self.md[-1]:
                # Remove the formatting if there is no data between.
                # TODO: doesn't work for multiple active formattings
                for _ in range(2):
                    del self.md[-1]
            del self.active_formatting[formatting]

        # Formatting needs to be on the same line to be valid.
        # Thus add newlines at the end.
        self.add_newlines(newlines)

    def data(self, data: str):
        if data in [
            "Content not supported",
            "This block is a placeholder for Tasks, which has been officially "
            "released on the newest version of Evernote and is no longer supported "
            "on this version. Deleting or moving this block may cause unexpected "
            "behavior in newer versions of Evernote.",
        ]:
            return  # ignore these texts

        if not data.strip() and (not self.md or not self.md[-1].strip()):
            # Skip the current whitespace:
            # - if the document is empty
            # - if the previous data contains only whitespace, too
            return

        if (
            self.active_lists
            and self.md
            and any(self.md[-1].endswith(bullet) for bullet in ["- [x] ", "- [ ] ", "- ", "1. "])
        ):
            # Normalize whitespaces at the start of list items.
            data = data.lstrip()

        if self.encryption is not None:
            # https://help.evernote.com/hc/en-us/articles/208314128-What-type-of-encryption-does-Evernote-use
            # https://soundly.me/decoding-the-Evernote-en-crypt-field-payload/
            if self.encryption["cipher"] != "AES" or self.encryption["length"] != "128":
                self.md.extend([data, "\n"])
                LOGGER.warning(
                    f"Could not decrypt. Unsupported cipher: "
                    f'"{self.encryption["cipher"]} {self.encryption["length"]}"'
                )
                return

            plaintext = decrypt(data, self.password.encode("utf-8"))
            if plaintext is None:
                self.md.extend([data, "\n"])
            else:
                # Process the decoded data.
                parser = ET.XMLParser(target=EnexToMarkdown(self.password))
                try:
                    parser.feed(plaintext)
                except ET.ParseError as exc:
                    self.md.extend([data, "\n"])
                    LOGGER.warning("Failed to parse decrypted text")
                    LOGGER.debug(exc, exc_info=True)
                    return

                # Insert decoded data to the existing data.
                decoded_md, decoded_hashes = parser.close()
                self.md.extend(decoded_md)
                self.hashes.extend(decoded_hashes)
            return

        if self.quote_level > 0 and self.md and self.md[-len(self.active_formatting) - 1] == "\n":
            # insert before any active formatting
            self.md.insert(-len(self.active_formatting), "> " * self.quote_level)

        if self.active_link:
            # https://stackoverflow.com/a/2052206/7410886
            title = self.active_link.get("title", "")
            self.active_link["title"] = title + data
        elif self.active_resource:
            LOGGER.warning(f"Resource title not handled: {self.active_resource['hash']}")
        else:
            target = self.table_cell if self.in_table else self.md
            target.append(data)

    def close(self):
        return "".join(self.md), self.hashes
