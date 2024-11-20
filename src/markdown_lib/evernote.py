"""Convert the enex (xml) note content to Markdown."""

import copy

import markdown_lib


# TODO: simplify
# pylint: disable=too-many-instance-attributes,too-many-branches,too-many-statements


class EnexToMarkdown:
    """https://docs.python.org/3/library/xml.etree.elementtree.html#xmlparser-objects"""

    def __init__(self, password, logger):
        self.password = password
        self.logger = logger

        self.global_level = 0
        self.active_lists = []
        self.active_formatting = {}
        self.active_link = {}
        self.active_resource = {}
        self.encrypted = False
        self.in_table = False
        self.table_row = []
        self.table_cell = []
        self.current_table = markdown_lib.common.MarkdownTable()
        self.quote_level = 0
        self.newlines_after_formatting = 0
        self.hashes = []
        self.md = []

    def add_newlines(self, count: int):
        """Add as many newlines as needed. Consider preceding newlines."""
        # TODO: check for simpler implementation
        if not self.md:
            return
        # how many newlines are at the end already?
        index = 0
        while index < len(self.md) and index < count and self.md[-index - 1] == "\n":
            index += 1
        # print(count, index, self.md)
        # insert missing newlines
        if index > 0:
            self.md[-index:] = ["\n"] * count
        else:
            self.md.extend(["\n"] * count)
        # print(self.md)

    def start(self, tag, attrib):
        self.global_level += 1
        # if tag != "div":
        #     print("="*20, tag, self.global_level)

        match tag:
            case "a":
                # link
                self.active_link["href"] = attrib.get("href")
                if (rel := attrib.get("rel")) is not None:  # TODO: correct?
                    self.active_link["title"] = rel
                elif (name := attrib.get("name")) is not None:
                    self.active_link["title"] = name
            case "b" | "strong":
                if "bold" in self.active_formatting:
                    return
                self.md.append("**")
                self.active_formatting["bold"] = self.global_level
            case "br":
                self.add_newlines(1)
            case "blockquote":
                self.quote_level += 1
                # TODO: prepend before each data or only once?
                self.md.append("> " * self.quote_level)
            case "center" | "div" | "font" | "en-note" | "span":
                pass  # only interested in attributes and data
            case "code":
                if "code" in self.active_formatting:
                    return
                self.md.append("`")
                self.active_formatting["code"] = self.global_level
            case "en-crypt":
                self.encrypted = True
                # https://github.com/akosbalasko/yarle/blob/2dfa5ff9d23414d3c23245327b435a96283cb8fe/src/utils/decrypt.ts#L51
                # TODO
            case "en-media":
                # inline resource (base64 encoded)
                self.active_resource = {"hash": attrib["hash"]}
            case "h1" | "h2" | "h3" | "h4" | "h5" | "h6" | "h7":
                self.add_newlines(2)  # ensure empty line
                self.md.append("#" * int(tag[-1]) + " ")
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
                    self.md.append(
                        f"![{attrib.get("title", attrib.get("alt", ""))}]({url})"
                    )
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
                    bullet = (
                        "[x] " if attrib.get("checked") in [True, "true"] else "[ ] "
                    )
                else:
                    # in a <div>
                    # TODO: integrate in active_lists
                    self.add_newlines(2)  # ensure empty line
                    bullet = (
                        "- [x] "
                        if attrib.get("checked") in [True, "true"]
                        else "- [ ] "
                    )
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
                self.logger.warning(f"ignoring opening tag {tag}")

        for key, value in attrib.items():
            match key:
                case "style":
                    # TODO: other styles
                    style_splitted = [v.strip() for v in value.split(";") if v.strip()]
                    for s in style_splitted:
                        try:
                            style, v = s.split(":", maxsplit=1)
                            style = style.strip()
                            v = v.strip()
                        except ValueError:
                            continue  # TODO
                        match style:
                            case "-en-codeblock" | "--en-codeblock":
                                if v == "true":
                                    self.add_newlines(2)  # ensure empty line
                                    self.md.append("```")
                                    self.add_newlines(1)
                                    self.active_formatting["codeblock"] = (
                                        self.global_level
                                    )
                            case "-evernote-highlight":
                                if v == "true" and "bold" not in self.active_formatting:
                                    # highlight is converted to bold
                                    self.md.append("**")
                                    self.active_formatting["bold"] = self.global_level
                            case "--en-id":
                                # will be replaced with tasks later
                                self.md.append(f"tasklist://{v}")
                            # case "--en-todo":
                            #     if v == "true":
                            #         self.active_lists.append("tasklist")
                            case "font-style":
                                # https://developer.mozilla.org/en-US/docs/Web/CSS/font-style
                                if (
                                    v == "italic"
                                    and "italic" not in self.active_formatting
                                ):
                                    self.md.append("*")
                                    self.active_formatting["italic"] = self.global_level
                                # TODO: handle v == "normal"?
                            case "font-weight":
                                if (
                                    v in ["bold", "bolder"]
                                    or v.isdigit()
                                    and int(v) >= 700
                                ) and "bold" not in self.active_formatting:
                                    # https://www.w3schools.com/cssref/pr_font_weight.php
                                    # 700 and above is bold
                                    self.md.append("**")
                                    self.active_formatting["bold"] = self.global_level
                                elif (
                                    v == "italic"
                                    and "italic" not in self.active_formatting
                                ):
                                    self.md.append("*")
                                    self.active_formatting["italic"] = self.global_level
                            # TODO: padding-left:40px;
                            # case "padding-left":
                            #     pass
                            # for debugging only
                            # case _:
                            #     print(style, v)
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
                    self.logger.warning(
                        f'tag "{tag}", ignoring attribute "{key}: {value}"'
                    )

    def end(self, tag):
        if self.encrypted:
            return  # TODO: implement encryption?

        newlines = 0
        match tag:
            case "a":
                # internal note link
                title = self.active_link.get("title")
                url = self.active_link["href"]
                if title is None and url is None:
                    pass
                elif title is None or title == url:
                    # normal link
                    self.md.append(f"<{url}>")
                elif url is None or url.strip() == "#":
                    # no URL to link
                    self.md.append(title)
                # elif url.startswith("data:image/"):
                #     # data:image/ resources seem to be duplicated
                #     # TODO: Is this always the case?
                #     pass
                else:
                    # normal link
                    self.md.append(f"[{title}]({url})")
                self.active_link = {}
            case (
                "b"
                | "i"
                | "s"
                | "u"
                | "center"
                | "cite"
                | "code"
                | "em"
                | "font"
                | "strong"
            ):
                pass  # handled already in active_formatting, TODO: sanity check
            case "br" | "div":
                newlines = 1
            case "blockquote":
                self.quote_level -= 1
            case "en-crypt":
                self.encrypted = False
            case "en-media":
                self.md.append(
                    f"![{self.active_resource.get("title", "")}]"
                    f"({self.active_resource["hash"]})"
                )
                self.hashes.append(self.active_resource["hash"])
                self.active_resource = {}
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
                self.current_table = markdown_lib.common.MarkdownTable()
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
                    self.logger.debug(f"Expected list '{list_type}', actual '{tag}'")
            case "li":
                pass
            case _:
                self.logger.warning(f"ignoring closing tag {tag}")

        self.global_level -= 1
        # if tag != "div":
        #     print("-"*20, tag, self.global_level)
        #     if self.active_link:
        #         print(self.active_link)
        #     if self.active_formatting:
        #         print(self.active_formatting)
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
                    self.logger.warning(f'unhandled formatting "{formatting}"')
            del self.active_formatting[formatting]

        # Formatting needs to be on the same line to be valid.
        # Thus add newlines at the end.
        self.add_newlines(newlines)

    def data(self, data):
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
            # - if the previous char is a whitespace, too
            return

        if self.active_link:
            # TODO: simplify
            if "title" in self.active_link:
                self.active_link["title"] += data
            else:
                self.active_link["title"] = data
        elif self.active_resource:
            self.logger.warning(
                f"Resource title not handled: {self.active_resource["hash"]}"
            )
        else:
            target = self.table_cell if self.in_table else self.md
            target.append(data)

    def close(self):
        return "".join(self.md), self.hashes
