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

from bs4 import BeautifulSoup

LOGGER = logging.getLogger("jimmy")
HTML_HEADER_RE = re.compile(r"^h[1-6]$")


def div_checklists(soup: BeautifulSoup):
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


def highlighting(soup: BeautifulSoup):
    """Remove all attributes and enable the "mark" extension to get highlighting."""
    for mark in soup.find_all("mark"):
        mark.attrs = {}


def iframes_to_links(soup: BeautifulSoup):
    """Convert iframes to simple links."""
    for iframe in soup.find_all("iframe"):
        iframe.name = "a"
        if iframe.text is None or not iframe.text.strip():  # link without text
            iframe.string = iframe.attrs.get("title", iframe.attrs["src"])
        iframe.attrs = {"href": iframe.attrs["src"]}


def merge_single_element_lists(soup: BeautifulSoup):
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


def multiline_markup(soup: BeautifulSoup):
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


def nimbus_note_streamline_lists(soup: BeautifulSoup):
    # - all lists are unnumbered lists (ul)
    #   - type is in the class attr (list-item-number, -bullet, -checkbox)
    # - indentation is in the class attr (indent-0)
    for list_ in soup.find_all("ul"):
        current_indent = 0
        current_list = list_
        for item in list_.find_all("li"):
            item_type = [
                i[len("list-item-") :]
                for i in item["class"]
                if i.startswith("list-item-")
            ][0]
            list_type = {"checkbox": "ul", "bullet": "ul", "number": "ol"}[item_type]
            if item_type == "checkbox":
                item.insert(0, soup.new_tag("input", type="checkbox"))

            indent = [i for i in item["class"] if i.startswith("indent-")][0]
            indent_int = int(indent[len("indent-") :])  # 1 digit number always
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


def notion_streamline_lists(soup: BeautifulSoup):
    # Checklists are unnumbered lists with special classes.
    for list_ in soup.find_all("ul", class_="to-do-list"):
        for item in list_.find_all("li"):
            checked_item = item.find("div")
            checked_item.name = "input"
            checked_item.attrs["type"] = "checkbox"
            if "checkbox-on" in checked_item.get("class", []):
                checked_item.attrs["checked"] = ""  # remove this key for unchecking


def remove_bold_header(soup: BeautifulSoup):
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


def remove_empty_elements(soup: BeautifulSoup):
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


def replace_special_characters(soup: BeautifulSoup):
    # https://www.w3.org/TR/html4/intro/sgmltut.html#h-3.2.3
    # TODO: These characters shouldn't be present in the first case.
    ignore_tags = ("annotation", "code", "kbd", "samp", "pre", "var")
    for element in soup.find_all(
        string=lambda value: value is not None and ("<" in value or ">" in value)
    ):
        if element.name in ignore_tags or element.find_parents(ignore_tags):
            continue
        nested_soup = BeautifulSoup(element.text, "html.parser")
        element.replace_with(nested_soup)


def synology_note_station_fix_img_src(soup: BeautifulSoup):
    # In the original nsx data, the "src" is stored in the
    # "ref" attribute. Move it where it belongs.
    for img in soup.find_all(
        "img",
        class_="syno-notestation-image-object",
        src="webman/3rdparty/NoteStation/images/transparent.gif",
    ):
        if (new_src := img.attrs.get("ref")) is not None:
            img.attrs["src"] = new_src


def streamline_tables(soup: BeautifulSoup):
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
        tags_to_remove = ["div", "span"]
        for tag in tags_to_remove:
            for element in table.find_all(tag):
                element.unwrap()

        # another hack: Replace any newlines (<p>, <br>) with a temporary string
        # and with <br> after conversion to markdown.
        def is_leading_or_trailing_whitespace(item) -> bool:
            if None in (item.previous_sibling, item.next_sibling):
                return True
            if item.previous_sibling.name in ("br", "p") or item.next_sibling.name in (
                "br",
                "p",
            ):
                return True
            return (
                not item.previous_sibling.text.strip()
                or not item.next_sibling.text.strip()
            )

        for item in table.find_all("br") + table.find_all("p"):
            if not is_leading_or_trailing_whitespace(item):
                item.append(soup.new_string("{TEMPORARYNEWLINE}"))
            item.unwrap()

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


def whitespace_in_math(soup: BeautifulSoup):
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
