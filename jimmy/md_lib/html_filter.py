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

import bs4

LOGGER = logging.getLogger("jimmy")
HTML_HEADER_RE = re.compile(r"^h[1-6]$")


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
    """Convert iframes to simple links."""
    for iframe in soup.find_all("iframe"):
        iframe.name = "a"
        if iframe.text is None or not iframe.text.strip():  # link without text
            iframe.string = iframe.attrs.get("title", iframe.attrs["src"])
        iframe.attrs = {"href": iframe.attrs["src"]}


def _to_markdown_header_id(text: str) -> str:
    """
    Convert any (header) text to a Markdown header ID.
    See: https://pandoc.org/MANUAL.html#extension-auto_identifiers

    >>> _to_markdown_header_id("Heading identifiers in HTML")
    'heading-identifiers-in-html'
    >>> _to_markdown_header_id("Maître d'hôtel")
    'maître-dhôtel'
    >>> _to_markdown_header_id("*Dogs*?--in *my* house?")
    'dogs--in-my-house'
    >>> _to_markdown_header_id("[HTML], [S5], or [RTF]?")
    'html-s5-or-rtf'
    >>> _to_markdown_header_id("3. Applications")
    'applications'
    >>> _to_markdown_header_id("33")
    'section'
    """
    # Remove all non-alphanumeric characters, except underscores, hyphens, and periods.
    text = "".join(
        [
            character
            for character in text
            if (character.isalnum() or character in (" ", "_", "-"))
        ]
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
        if character.isalpha() or found_first_letter:
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
        match linebreak.parent.name:
            case (
                "b"
                | "cite"
                | "code"
                | "del"
                | "em"
                # TODO: "font"
                | "i"
                | "ins"
                | "s"
                | "strike"
                | "strong"
                | "sub"
                | "sup"
                | "tt"
                | "u"
            ):
                # wrap all siblings
                for linebreak_sibling in itertools.chain(
                    linebreak.previous_siblings, linebreak.next_siblings
                ):
                    if linebreak_sibling.name not in ("br", "p"):
                        linebreak_sibling.wrap(soup.new_tag(linebreak.parent.name))
                linebreak.parent.unwrap()
            case "h1" | "h2" | "h3" | "h4" | "h5" | "h6":
                linebreak.decompose()


def nimbus_note_add_mark(soup: bs4.BeautifulSoup):
    for highlighted_element in soup.find_all(attrs={"data-highlight": True}):
        if highlighted_element.attrs["data-highlight"] == "transparent":
            continue
        wrap_content(soup, highlighted_element, "mark")
    for highlighted_element in soup.find_all(attrs={"data-block-background": True}):
        if highlighted_element.attrs["data-block-background"] == "transparent":
            continue
        wrap_content(soup, highlighted_element, "mark")


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
        if "outline-list-item" in classes or "list-item-bullet" in classes:
            item_type = "bullet"
        elif "list-item-number" in classes:
            item_type = "number"
        elif "list-item-checkbox" in classes:
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
                item.insert(0, soup.new_tag("input", type="checkbox"))

            indent_int = get_indentation_level(item)
            if indent_int == 0:
                # would be sufficient to do only one time
                current_list.name = list_type
                if item_type == "checkbox" and "checklist" not in current_list["class"]:
                    current_list["class"] = ["checklist"]  # drop the other classes
            if indent_int > current_indent:
                # new child list
                new_list = soup.new_tag(list_type)
                current_list.append(new_list)
                current_list = new_list
                current_indent = indent_int
            elif indent_int < current_indent:
                # find parent list at the corresponding level
                for _ in range(current_indent - indent_int):
                    current_list = current_list.parent

            item.attrs = {}  # remove all attributes
            current_list.append(item)


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
            style=lambda value: value is not None and "font-weight: bold" in value
        )

    for header in soup.find_all(HTML_HEADER_RE):
        for bold in find_all_bold(header):
            bold.unwrap()

    for bold in find_all_bold(soup):
        for header in bold.find_all(HTML_HEADER_RE):
            header.unwrap()


def remove_empty_elements(soup: bs4.BeautifulSoup):
    # Remove empty elements.
    # TODO: not activated - too many false positives
    def is_empty(element):
        return (
            len(element.get_text(strip=True)) == 0
            and not element.contents
            and not element.is_empty_element
            # exclude:
            # - usually self-closing tags, but sometimes not
            # - images and links
            and element.name not in ("a", "br", "img", "input", "svg")
        )

    def remove_if_empty(element):
        if is_empty(element):
            parent = element.parent
            element.unwrap()  # unwrap to preserve spaces
            remove_if_empty(parent)

    for element in soup.find_all():
        remove_if_empty(element)


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
        for index, list_item in enumerate(
            list_.find_all("li", recursive=False), start=1
        ):
            # handle nested lists
            for nested_list in list_item.find_all(["ul", "ol"], recursive=False):
                simplify_list(nested_list, level=level + 1)

            if list_item.text is None:
                continue
            bullet = "- " if list_.name == "ul" else f"{index}. "
            list_item.string = (
                "{TEMPORARYNEWLINE}" + "&nbsp;" * level * 4 + bullet + list_item.text
            )
            list_item.unwrap()
        list_.unwrap()

    for table in soup.find_all("table"):
        # Remove nested tables.
        for nested_table in table.find_all("table"):
            nested_table.unwrap()  # TODO: revisit

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
        for list_ in table.find_all(
            lambda e: e.name in ("ul", "ol") and e.parent.name != "li"
        ):
            simplify_list(list_)

        for row_index, row in enumerate(table.find_all("tr")):
            for td in row.find_all("td"):
                # tables seem to be headerless always
                # make first row to header
                if row_index == 0:
                    td.name = "th"

        # headers are not supported - convert to bold
        for header in table.find_all(HTML_HEADER_RE):
            header.name = "strong"

        # blockquotes are not supported - convert to inline quote
        for quote in table.find_all("blockquote"):
            quote.name = "q"

        # remove "tbody"
        if (body := table.find("tbody")) is not None:
            body.unwrap()

        table.attrs = {}


def whitespace_in_math(soup: bs4.BeautifulSoup):
    """
    - Escape unescaped newlines inside tex math blocks.
    - Strip trailing (escaped) whitespace.
    """
    for annotation in soup.find_all("annotation"):
        if (encoding := annotation.attrs.get("encoding")) != "application/x-tex":
            LOGGER.debug(f'Unsupported annotation encoding "{encoding}"')
            continue
        annotation.string = annotation.text.rstrip("\\" + string.whitespace).replace(
            "\n\n", "\n"
        )
