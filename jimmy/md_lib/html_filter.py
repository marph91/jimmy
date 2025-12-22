"""
HTML preprocessing functions to prepare for Pandoc conversion.

Should be used:
- For format specific conversions.
- If they can't be expressed in another way.
"""

import itertools
import logging
import re
import string
import urllib.parse

import bs4

import jimmy.md_lib.common

LOGGER = logging.getLogger("jimmy")
HTML_HEADER_RE = re.compile(r"^h[1-6]$")


def extract_styles(tag) -> dict[str, str]:
    styles: dict[str, str] = {}
    for style_str in tag.get("style", "").split(";"):
        if not style_str:
            return styles
        style_str_split = style_str.split(":", maxsplit=1)
        match len(style_str_split):
            case 1:
                key = style_str_split[0]
                value = ""
            case 2:
                key, value = style_str_split
        styles[key.strip()] = value.strip()
    return styles


def wrap_content(soup, element, tag: str):
    """Wrap the content of an element."""
    new_element = soup.new_tag(tag)
    for content in reversed(element.contents):
        new_element.insert(0, content.extract())

    element.append(new_element)


def div_checklists(soup: bs4.BeautifulSoup):
    """Convert div checklists to plain HTML checklists."""
    # reverse to handle nested lists first
    for task_list in reversed(soup.find_all("div", class_="checklist")):
        task_list.name = "ul"
        # remove the spans
        for span in task_list.find_all("span"):
            span.unwrap()
        # remove the first divs
        for child in task_list.children:
            if child.name == "div":
                child.unwrap()
        # convert the second divs to list items
        for child in task_list.children:
            if child.name == "div":
                child.name = "li"


def highlighting(soup: bs4.BeautifulSoup):
    """Remove all attributes and enable the "mark" extension to get highlighting."""
    for mark in soup.find_all("mark"):
        mark.attrs = {}


def iframes_to_links(soup: bs4.BeautifulSoup):
    """
    Convert iframes to simple links.

    >>> soup = bs4.BeautifulSoup('<iframe src="https://kicker.de"></iframe>', "html.parser")
    >>> iframes_to_links(soup)
    >>> soup
    <a href="https://kicker.de">https://kicker.de</a>

    >>> soup = bs4.BeautifulSoup('<iframe src="https://kicker.de">&nbsp;</iframe>', "html.parser")
    >>> iframes_to_links(soup)
    >>> soup
    <a href="https://kicker.de">https://kicker.de</a>

    >>> soup = bs4.BeautifulSoup('<iframe src="https://kicker.de">link</iframe>', "html.parser")
    >>> iframes_to_links(soup)
    >>> soup
    <a href="https://kicker.de">link</a>
    """
    for iframe in soup.find_all("iframe"):
        if not iframe.attrs.get("src", ""):
            iframe.decompose()
            continue
        iframe.name = "a"
        if iframe.text is None or not iframe.text.strip():  # link without text
            iframe.string = iframe.attrs.get("title", iframe.attrs["src"])
        iframe.attrs = {"href": iframe.attrs["src"]}


def _to_markdown_header_id(text: str) -> str:
    """
    Convert any (header) text to a Markdown header ID.
    See: https://pandoc.org/MANUAL.html#extension-auto_identifiers
    Slightly adapted to work in Firefox and VSCode.

    >>> _to_markdown_header_id("Heading identifiers in HTML")
    'heading-identifiers-in-html'
    >>> _to_markdown_header_id("Maître d'hôtel")
    'maître-dhôtel'
    >>> _to_markdown_header_id("*Dogs*?--in *my* house?")
    'dogs--in-my-house'
    >>> _to_markdown_header_id("[HTML], [S5], or [RTF]?")
    'html-s5-or-rtf'
    >>> _to_markdown_header_id("3. Applications")
    '3-applications'
    >>> _to_markdown_header_id("4-х актная  структура выступления (монолога)")
    '4-х-актная-структура-выступления-монолога'
    >>> _to_markdown_header_id("")
    'section'
    """
    # Reduce consecutive whitespaces.
    text = " ".join(text.split())
    # Remove all non-alphanumeric characters, except underscores, hyphens, and periods.
    text = "".join(
        [character for character in text if (character.isalnum() or character in (" ", "_", "-"))]
    )
    # Replace all spaces and newlines with hyphens.
    text = text.replace(" ", "-").replace("\n", "-")
    # Convert all alphabetic characters to lowercase.
    text = text.lower()
    # Remove everything up to the first letter (identifiers may not begin with a number
    # or punctuation mark).
    new_text = []
    found_first_letter = False
    for character in text:
        if character.isalnum() or found_first_letter:
            new_text.append(character)
            found_first_letter = True
    text = "".join(new_text)
    # If nothing is left after this, use the identifier section.
    if not text:
        text = "section"
    return text


def link_internal_headings(soup: bs4.BeautifulSoup):
    """
    Replace internal link IDs with their corresponding header ID.
    Only consider headings, since they can be linked in markdown later.
    All other IDs are stripped away.
    """
    href_elements = soup.find_all(href=True)
    for element in href_elements:
        if not (id_ := element.get("href", "")).startswith("#"):
            continue
        linked_element = soup.find(id=id_[1:])
        if (
            linked_element is None
            or linked_element.name is None
            or not linked_element.name.startswith("h")
        ):
            continue
        element.attrs["href"] = "#" + _to_markdown_header_id(linked_element.text)


INLINE_FORMATTING_TAGS = [
    "b",
    "cite",
    "code",
    "del",
    "em",
    "i",
    "ins",
    "mark",
    "s",
    "strike",
    "strong",
    "sub",
    "sup",
    "tt",
    "u",
]


def merge_consecutive_formatting(soup: bs4.BeautifulSoup):
    for inline_formatting_tag in INLINE_FORMATTING_TAGS:
        for tag in soup.find_all(inline_formatting_tag):
            # first case: parent element has the tag already
            if tag.find_parents(inline_formatting_tag):
                # TODO: move this to a separate function
                tag.unwrap()  # remove tag, if any parent element has the tag already
                continue

            # second case: previous element has the same tag
            if (
                tag.previous_sibling is not None
                and tag.previous_sibling.name == inline_formatting_tag
            ):
                tag.previous_sibling.append(tag)
                tag.unwrap()

            # third case: previous element of the parent element has the same tag
            if len(tuple(itertools.chain(tag.previous_siblings, tag.next_siblings))) > 0:
                # Apply only if this is the only tag at this level.
                # Else some additional splitting would be needed.
                continue

            toplevel_with_siblings = tag

            # find the next parent element with siblings
            while True:
                toplevel_with_siblings = toplevel_with_siblings.parent
                if (
                    toplevel_with_siblings is None
                    or len(
                        tuple(
                            itertools.chain(
                                toplevel_with_siblings.previous_siblings,
                                toplevel_with_siblings.next_siblings,
                            )
                        )
                    )
                    > 0
                ):
                    break
            if toplevel_with_siblings is None:
                continue

            # check if it has the same tag
            if (
                toplevel_with_siblings.previous_sibling is not None
                and toplevel_with_siblings.previous_sibling.name == inline_formatting_tag
            ):
                # Merge the elements with same formatting and remove the duplicated formatting
                # afterwards.
                toplevel_with_siblings.previous_sibling.append(toplevel_with_siblings)
                tag.unwrap()


def merge_single_element_lists(soup: bs4.BeautifulSoup):
    """
    Notion lists and odt lists sometimes contain only one item.
    Append the current item to the previous list if possible.
    """
    # TODO: doctest
    for list_ in soup.find_all(["ul", "ol"]):
        if len(list_.find_all("li")) == 1:
            for potential_list in list_.previous_siblings:
                if potential_list is None:
                    continue
                if potential_list.name == list_.name:
                    potential_list.append(list_)
                    list_.unwrap()
                elif not potential_list.text.strip():
                    continue
                break  # either it's the first matching sibling or we break


def multiline_markup(soup: bs4.BeautifulSoup):
    for linebreak in soup.find_all(["br", "p"]):
        # https://www.w3schools.com/html/html_formatting.asp
        if linebreak.parent.name in INLINE_FORMATTING_TAGS:
            # wrap all siblings
            for linebreak_sibling in itertools.chain(
                linebreak.previous_siblings, linebreak.next_siblings
            ):
                if linebreak_sibling.name not in ("br", "p"):
                    linebreak_sibling.wrap(soup.new_tag(linebreak.parent.name))
            linebreak.parent.unwrap()
        elif linebreak.parent.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            linebreak.decompose()


def nimbus_note_add_mark(soup: bs4.BeautifulSoup):
    # old editor
    for highlighted_element in soup.find_all(class_="nn-marker"):
        wrap_content(soup, highlighted_element, "mark")
    # new editor
    for highlight_attribute in [
        "data-highlight",
        "data-block-background",
        "data-comment-color",
        "data-palette-bg-rgb",  # table cells
    ]:
        for highlighted_element in soup.find_all(attrs={highlight_attribute: True}):
            if highlighted_element.attrs[highlight_attribute] in ("transparent", "white"):
                continue
            wrap_content(soup, highlighted_element, "mark")


def nimbus_note_add_note_links(soup: bs4.BeautifulSoup):
    # note links are represented by "mention" tags
    for mention_link in soup.find_all("span", class_="mention-link"):
        if (mention_type := mention_link.attrs.get("data-mention-type", "")) != "note":
            LOGGER.debug(f"Unexpected mention type: {mention_type}")
        if not (mention_name := mention_link.attrs.get("data-mention-name", "")) and not (
            mention_name := mention_link.text
        ):
            LOGGER.debug("Couldn't add link. Link name and text is empty.")
            continue
        # TODO: check if linking by ID is possible
        mention_link.parent.replace_with(
            soup.new_tag(
                "a",
                attrs={"href": f"nimbusnote://{urllib.parse.quote(mention_name)}"},
                string=mention_link.get_text(),
            )
        )


def nimbus_note_streamline_lists(soup: bs4.BeautifulSoup):
    # - all lists are unnumbered lists (ul)
    #   - type is in the class attr
    #     (outline-list-item or list-item-number, -bullet, -checkbox)
    # - indentation is in the class attr (indent-X or level-X)

    def get_indentation_level(item) -> int:
        for class_ in item.get("class", []):
            if class_.startswith("indent-"):
                return int(class_[len("indent-") :])
            if class_.startswith("level-"):
                return int(class_[len("level-") :])
        LOGGER.debug("Couldn't detect indentation. Set to '0'.")
        return 0

    def get_list_item_type(item) -> tuple[str, str]:
        classes = item.get("class", [])
        parent_classes = item.parent.get("class", [])
        if "outline-list-item" in classes or "list-item-bullet" in classes:
            item_type = "bullet"
        elif "list-item-number" in classes:
            item_type = "number"
        elif (
            "list-item-checkbox" in classes
            or "nn-checkbox-list" in parent_classes
            or "checklist" in parent_classes
        ):
            item_type = "checkbox"
        else:
            LOGGER.debug("Couldn't detect list type. Set to 'unnumbered'.")
            item_type = "bullet"
        list_type = {"checkbox": "ul", "bullet": "ul", "number": "ol"}[item_type]
        return list_type, item_type

    for list_ in soup.find_all("ul"):
        current_indent = 0
        current_list = list_
        for item in list_.find_all("li"):
            list_type, item_type = get_list_item_type(item)
            if item_type == "checkbox":
                input_element = soup.new_tag("input", type="checkbox")
                if item.attrs.get("data-checked", "false") == "true" or "nn-checked" in item.get(
                    "class", []
                ):
                    input_element.attrs["checked"] = ""  # checkbox is checked
                item.attrs.pop("data-checked", None)
                item.insert(0, input_element)

            indent_int = get_indentation_level(item)
            if indent_int == 0:
                # would be sufficient to do only one time
                current_list.name = list_type
                if item_type == "checkbox" and "checklist" not in current_list.get("class", []):
                    current_list["class"] = ["checklist"]  # drop the other classes
            if indent_int > current_indent:
                # new child list
                new_list = soup.new_tag(list_type)
                current_list.append(new_list)
                current_list = new_list
            elif indent_int < current_indent:
                # find parent list at the corresponding level
                for _ in range(current_indent - indent_int):
                    current_list = current_list.parent
            current_indent = indent_int

            item.attrs = {}  # remove all attributes
            current_list.append(item)

    # special case: single checkboxes in tables
    for checkbox in soup.find_all("span", class_="checkbox-component"):
        # Use the temporary strings here, because the checkbox brackets
        # would be escaped by pandoc.
        if "checked" in checkbox.get("class", []):
            checkbox.string = "{TEMPORARYCHECKBOXCHECKED}"
        else:
            checkbox.string = "{TEMPORARYCHECKBOXUNCHECKED}"


def nimbus_note_streamline_tables(soup: bs4.BeautifulSoup):
    # remove:
    # - footer
    # - first row (only contains A, B, ...)
    # - first column (only contains 1, 2, ...)
    # - second column (empty)
    for table in soup.find_all("table"):
        # There is no useful information in Nimbus Note table footers.
        for table_footer in table.find_all("tfoot"):
            table_footer.decompose()

        # This seems to affect new tables only. Some sanity checks are needed.
        for row_index, row in enumerate(table.find_all("tr")):
            for col_index, col in enumerate(row.find_all("td")):
                text = col.text.strip()
                if row_index == 0 and text and not text.isalpha():
                    LOGGER.debug("Old table (first row). Skip streamlining.")
                    return
                if col_index in (0, 1) and text and not text.isdigit():
                    LOGGER.debug("Old table (first columns). Skip streamlining.")
                    return

        for row_index, row in enumerate(table.find_all("tr")):
            if row_index == 0:
                row.decompose()  # first row
            for col_index, col in enumerate(row.find_all("td")):
                if col_index in (0, 1):
                    col.decompose()  # first and second column


def nimbus_strip_images(soup: bs4.BeautifulSoup):
    # Strip all inline SVGs, since they add icons that are not visible in the original document.
    for svg in soup.find_all("svg"):
        svg.decompose()

    # Strip file size information.
    for file_size in soup.find_all("span", class_="file-size"):
        file_size.decompose()


def notion_streamline_lists(soup: bs4.BeautifulSoup):
    # Checklists are unnumbered lists with special classes.
    for list_ in soup.find_all("ul", class_="to-do-list"):
        for item in list_.find_all("li"):
            checked_item = item.find("div")
            checked_item.name = "input"
            checked_item.attrs["type"] = "checkbox"
            if "checkbox-on" in checked_item.get("class", []):
                checked_item.attrs["checked"] = ""  # remove this key for unchecking


def remove_bold_header(soup: bs4.BeautifulSoup):
    # Remove overlap of bold and header. Keep the outer element.
    def find_all_bold(parent):
        return parent.find_all(["b", "strong"]) + parent.find_all(
            lambda tag: "bold" in extract_styles(tag).get("font-weight", "")
        )

    for header in soup.find_all(HTML_HEADER_RE):
        for bold in find_all_bold(header):
            bold.unwrap()

    for bold in find_all_bold(soup):
        for header in bold.find_all(HTML_HEADER_RE):
            header.unwrap()


def remove_duplicated_links(soup: bs4.BeautifulSoup):
    # They are linked twice. We only want one link.
    # image links
    for img in soup.find_all("img"):
        img_src = img.attrs.get("src")
        if img.parent.attrs.get("href", "") == img_src:
            img.parent.unwrap()

    # web links
    for link in soup.find_all("a", href=True):
        link_url = link.attrs.get("href", "")
        for sublink in link.find_all("a", href=link_url):
            sublink.unwrap()


def remove_empty_markup(soup: bs4.BeautifulSoup):
    """
    >>> soup = bs4.BeautifulSoup('<b>\t</b>', "html.parser")
    >>> remove_empty_markup(soup)
    >>> soup
    <BLANKLINE>

    >>> soup = bs4.BeautifulSoup('<b></b>', "html.parser")
    >>> remove_empty_markup(soup)
    >>> soup
    <BLANKLINE>
    """

    def find_empty_markup(tag):
        # there should only be a single string as child
        children = list(tag.children)
        if len(children) == 1 and not isinstance(children[0], bs4.element.NavigableString):
            return False
        if len(children) > 1:
            return False
        return tag.name in INLINE_FORMATTING_TAGS and (
            tag.string is None or "\n" not in tag.string and not tag.string.strip()
        )

    empty_elements = soup.find_all(find_empty_markup)
    for empty_element in empty_elements:
        empty_element.unwrap()  # unwrap to preserve spaces


def replace_special_characters(soup: bs4.BeautifulSoup):
    # https://www.w3.org/TR/html4/intro/sgmltut.html#h-3.2.3
    # TODO: These characters shouldn't be present in the first case.
    ignore_tags = ("annotation", "code", "kbd", "samp", "pre", "var")
    for element in soup.find_all(
        string=lambda value: value is not None and ("<" in value or ">" in value)
    ):
        if element.name in ignore_tags or element.find_parents(ignore_tags):
            continue
        nested_soup = bs4.BeautifulSoup(element.text, "html.parser")
        element.replace_with(nested_soup)


def strikethrough(soup: bs4.BeautifulSoup):
    """
    >>> soup = bs4.BeautifulSoup(
    ...    '<span style="text-decoration: line-through">striketrough</span>', "html.parser")
    >>> strikethrough(soup)
    >>> soup
    <span style="text-decoration: line-through"><s>striketrough</s></span>
    """

    # support strikethrough by the style attributes
    def find_strikethrough_style(tag):
        styles = extract_styles(tag)
        return "line-through" in styles.get("text-decoration", "") or "line-through" in styles.get(
            "text-decoration-line", ""
        )

    for strikethrough_element in soup.find_all(find_strikethrough_style):
        wrap_content(soup, strikethrough_element, "s")


def synology_note_station_fix_checklists(soup: bs4.BeautifulSoup):
    # In the original nsx data, the checklists are plain div lists.
    # The indentation is stored in the divs "padding-left" attribute (multiple of 30 px).
    # The state is stored in the child divs attribute "syno-notestation-editor-checkbox-checked".
    def list_item_filter(tag):
        if tag.name != "div":
            return False
        input_tags = tag.find_all("input", class_="syno-notestation-editor-checkbox")
        first_child = next(tag.children, None)
        return len(input_tags) == 1 and first_child is not None and first_child.name != "div"

    for list_item in soup.find_all(list_item_filter):
        input_child = list_item.find("input")

        # find or create parent list
        if list_item.previous_sibling is not None and list_item.previous_sibling.name == "ul":
            list_item.previous_sibling.append(list_item)
        else:
            list_item.wrap(soup.new_tag("ul"))

        # parse the list level (f. e. "padding-left: 30px" is level 1)
        styles = extract_styles(list_item)
        padding_left = styles.get("padding-left", "0")
        level = int("".join([char for char in padding_left if char.isdigit()])) // 30

        # parent item can be
        # - a list (new item for existing list: ul -> li)
        # - a list item (new item in new list level: li -> ul)
        list_with_item = None
        parent_item = list_item.parent
        # go down as many levels as needed
        for loop_level in range(level):
            if (new_parent_item := parent_item.find("ul")) is None:
                # new list in last list item
                new_parent_item = next(reversed(parent_item.find_all("li")), None)
                if new_parent_item is None:
                    new_parent_item = parent_item  # fallback
                if loop_level == level - 1:
                    list_with_item = soup.new_tag("ul")
                    list_item.wrap(list_with_item)
                break
            parent_item = new_parent_item

        if list_with_item is None:
            parent_item.append(list_item)
        else:
            parent_item.append(list_with_item)

        # Move input element directly after "li". This is needed to convert to a checkbox.
        list_item.name = "li"
        while input_child.parent.name != "li":
            input_child.parent.parent.insert(0, input_child)

        # make the input child a checkbox
        new_attrs = {"type": "checkbox"}
        if "syno-notestation-editor-checkbox-checked" in input_child.get("class", []):
            new_attrs["checked"] = ""  # checkbox is checked
        input_child.attrs = new_attrs

        # remove parent attributes
        list_item.attrs = {}


def synology_note_station_fix_img_src(soup: bs4.BeautifulSoup):
    # In the original nsx data, the "src" is stored in the
    # "ref" attribute. Move it where it belongs.
    for img in soup.find_all(
        "img",
        class_="syno-notestation-image-object",
        src="webman/3rdparty/NoteStation/images/transparent.gif",
    ):
        if (new_src := img.attrs.get("ref")) is not None:
            img.attrs["src"] = new_src


NEWLINE_RE = re.compile(".*\n.*")


def streamline_tables(soup: bs4.BeautifulSoup):
    # all pipe tables need to be "simple" according to:
    # https://github.com/jgm/pandoc/blob/5766443bc89bababaa8bba956db5f798f8b60675/src/Text/Pandoc/Writers/Markdown.hs#L619
    # - no custom widths
    # - no linebreaks
    # However, in practice it seems to be a bit more complicated.

    def simplify_list(list_, level: int = 0):
        for index, list_item in enumerate(list_.find_all("li", recursive=False), start=1):
            # handle nested lists
            for nested_list in list_item.find_all(["ul", "ol"], recursive=False):
                simplify_list(nested_list, level=level + 1)

            if list_item.text is None:
                continue
            bullet = "- " if list_.name == "ul" else f"{index}. "
            list_item.string = "{TEMPORARYNEWLINE}" + "&nbsp;" * level * 4 + bullet + list_item.text
            list_item.unwrap()
        list_.unwrap()

    for table in soup.find_all("table"):
        # Remove nested tables.
        for nested_table in table.find_all("table"):
            nested_table.unwrap()  # TODO: revisit

        # Remove hidden cells, since they are respected by Pandoc.
        # For example Nimbus Note adds them when colspan or rowspan > 1.
        # But colspan and rowspan is respected by Pandoc, too. This results
        # in many unwanted cells.
        for hidden_cell in table.find_all("td", attrs={"hidden": True}):
            hidden_cell.decompose()

        # Remove all divs, since they cause pandoc to fail converting the table.
        # https://stackoverflow.com/a/32064299/7410886
        # Convert code blocks to inline code by removing the "pre" tag.
        # TODO: This could be problematic with multiline code.
        tags_to_remove = ["div", "pre", "span"]
        for tag in tags_to_remove:
            for element in table.find_all(tag):
                element.unwrap()

        # another hack: Replace any newlines (<p>, <br>) with a temporary string
        # and with <br> after conversion to markdown.
        def is_leading_whitespace(item) -> bool:
            if item.previous_sibling is None:
                return True
            if item.previous_sibling.name in ("br", "p"):
                return True
            return not item.previous_sibling.text.strip()

        def is_trailing_whitespace(item) -> bool:
            if item.next_sibling is None:
                return True
            if item.next_sibling.name in ("br", "p"):
                return True
            return not item.next_sibling.text.strip()

        for item in table.find_all("br") + table.find_all("p"):
            if not is_leading_whitespace(item) and not is_trailing_whitespace(item):
                item.append(soup.new_string("{TEMPORARYNEWLINE}"))
            item.unwrap()

        # another hack: Replace any newlines inside NavigableStrings ("\n")
        # like above.
        for table_cell in table.find_all(["th", "td"]):
            for item in table_cell.find_all(string=NEWLINE_RE):
                new_string = item
                # remove whitespaces if they are leading or trailing
                if is_leading_whitespace(item):
                    while new_string.startswith("\n"):
                        new_string = new_string[1:]
                if is_trailing_whitespace(item):
                    while new_string.endswith("\n"):
                        new_string = new_string[:-1]
                # keep all other whitespaces (in the intermediate form)
                new_string = new_string.replace("\n", "{TEMPORARYNEWLINE}")
                item.replace_with(new_string)

        # another hack: handle lists, i. e. replace items with "<br>- ..."
        # find only root lists (exclude nested lists)
        for list_ in table.find_all(lambda e: e.name in ("ul", "ol") and e.parent.name != "li"):
            simplify_list(list_)

        for row_index, row in enumerate(table.find_all("tr")):
            if row_index == 0:
                header_cells = row.find_all("td")
                if any(int(cell.attrs.get("rowspan", "1")) > 1 for cell in header_cells):
                    break  # don't convert cells over multiple rows to header cells
                for cell in header_cells:
                    # tables seem to be headerless always
                    # make first row to header
                    cell.name = "th"

        # headers are not supported - convert to bold
        for header in table.find_all(HTML_HEADER_RE):
            header.name = "strong"

        # blockquotes are not supported - convert to inline quote
        for quote in table.find_all("blockquote"):
            quote.name = "q"

        # remove "thead" and "tbody"
        for body_head in table.find_all(["thead", "tbody"]):
            body_head.unwrap()

        table.attrs = {}


def underline(soup: bs4.BeautifulSoup):
    """
    >>> soup = bs4.BeautifulSoup(
    ...    '<span style="text-decoration:underline">underline</span>', "html.parser")
    >>> underline(soup)
    >>> soup
    ++<span style="text-decoration:underline">underline</span>++

    >>> soup = bs4.BeautifulSoup('<u>underline</u>', "html.parser")
    >>> underline(soup)
    >>> soup
    ++underline++
    """

    # support underline by the style attributes
    def find_underline_style(tag):
        styles = extract_styles(tag)
        return "underline" in styles.get("text-decoration", "") or "underline" in styles.get(
            "text-decoration-line", ""
        )

    for underlined in soup.find_all(find_underline_style):
        underlined.insert_before(soup.new_string("++"))
        underlined.insert_after(soup.new_string("++"))

    # Underlining seems to be converted to italic by Pandoc.
    # Joplin supports the "++insert++"" syntax, but it seems to be not widely used.
    # Use HTML for underlining.
    # TODO: Check if there is a better solution.
    for underlined in soup.find_all(["ins", "u"]):
        underlined.insert_before(soup.new_string("++"))
        underlined.insert_after(soup.new_string("++"))
        underlined.unwrap()


def unwrap_inline_whitespace(soup: bs4.BeautifulSoup):
    """
    >>> soup = bs4.BeautifulSoup('<b> foo</b>', "html.parser")
    >>> unwrap_inline_whitespace(soup)
    >>> soup
     <b>foo</b>

    # TODO: nested markup with whitespace
    >>> soup = bs4.BeautifulSoup('<b><i> foo </i></b>', "html.parser")
    >>> unwrap_inline_whitespace(soup)
    >>> soup
    <b> <i>foo</i> </b>
    """

    def find_tags_with_leading_trailing_whitespace(tag):
        # there should only be a single string as child
        children = list(tag.children)
        if len(children) != 1 or not isinstance(children[0], bs4.element.NavigableString):
            return False
        return (
            tag.name in INLINE_FORMATTING_TAGS
            and tag.string is not None
            and "\n" not in tag.string
            and tag.string != tag.string.strip()
        )

    whitespace_elements = soup.find_all(find_tags_with_leading_trailing_whitespace)
    for whitespace_element in whitespace_elements:
        leading_whitespace, new_text, trailing_whitespace = (
            jimmy.md_lib.common.split_leading_trailing_whitespace(whitespace_element.string)
        )
        if leading_whitespace and whitespace_element.parent is not None:
            whitespace_element.insert_before(soup.new_string(leading_whitespace))
        if trailing_whitespace and whitespace_element.parent is not None:
            whitespace_element.insert_after(soup.new_string(trailing_whitespace))
        whitespace_element.string = new_text


def upnote_add_formula(soup: bs4.BeautifulSoup):
    for formula in soup.find_all(attrs={"data-upnote-formula": True}):
        formula.name = "annotation"
        formula.attrs = {"encoding": "application/x-tex"}
        formula.wrap(soup.new_tag("math", attrs={"display": "block"}))


def upnote_add_highlight(soup: bs4.BeautifulSoup):
    for highlight in soup.find_all(
        attrs={"class": lambda c: c.startswith("shine-highlight") if c else False}
    ):
        highlight.name = "mark"


def upnote_streamline_checklists(soup: bs4.BeautifulSoup):
    """
    >>> soup = bs4.BeautifulSoup(
    ...     '<ul><li data-checked="false"><div>Budget?</div></li></ul>', "html.parser")
    >>> upnote_streamline_checklists(soup)
    >>> soup
    <ul class="checklist"><li><input type="checkbox"/>Budget?</li></ul>
    """
    for list_ in soup.find_all("ul"):
        for item in list_.find_all("li", attrs={"data-checked": True}):
            input_element = soup.new_tag("input", type="checkbox")
            if item.attrs.get("data-checked", "false") == "true":
                input_element.attrs["checked"] = ""  # checkbox is checked
            item.attrs.pop("data-checked", None)
            item.insert(0, input_element)

            if "checklist" not in list_.get("class", []):
                list_["class"] = ["checklist"]  # drop the other classes

            # remove tags that would cause the checklist to not render properly
            tags_to_remove = ["div", "pre", "span"]
            for tag in tags_to_remove:
                for element in item.find_all(tag):
                    element.unwrap()


def whitespace_in_math(soup: bs4.BeautifulSoup):
    """
    - Escape unescaped newlines inside tex math blocks.
    - Strip trailing (escaped) whitespace.
    """
    for annotation in soup.find_all("annotation"):
        if (encoding := annotation.attrs.get("encoding")) != "application/x-tex":
            LOGGER.debug(f'Unsupported annotation encoding "{encoding}"')
            continue
        annotation.string = annotation.text.rstrip("\\" + string.whitespace).replace("\n\n", "\n")
