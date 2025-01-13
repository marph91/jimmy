"""HTML preprocessing functions to prepare for Pandoc conversion."""

from bs4 import BeautifulSoup


def div_checklists(soup: BeautifulSoup):
    """Convert div checklists to plain HTML checklists."""
    for task_list in soup.find_all("div", class_="checklist"):
        task_list.name = "ul"
        # remove the spans
        for span in task_list.find_all("span"):
            span.unwrap()
        # remove the first divs
        for child in task_list.children:
            child.unwrap()
        # convert the second divs to list items
        for child in task_list.children:
            child.name = "li"


def iframes_to_links(soup: BeautifulSoup):
    """Convert iframes to simple links."""
    for iframe in soup.find_all("iframe"):
        iframe.name = "a"
        if iframe.string is None or not iframe.string.strip():  # link without text
            iframe.string = iframe.attrs.get("title", iframe.attrs["src"])
        iframe.attrs = {"href": iframe.attrs["src"]}


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
            checked_item = item.findChild("div")
            checked_item.name = "input"
            checked_item.attrs["type"] = "checkbox"
            if "checkbox-on" in checked_item.get("class", []):
                checked_item.attrs["checked"] = ""  # remove this key for unchecking

    # Notion lists seem to contain always only one item.
    # Append the current item to the list if possible.
    for list_ in soup.find_all(["ul", "ol"]):
        if (
            previous_sibling := list_.previous_sibling
        ) is not None and previous_sibling.name == list_.name:
            previous_sibling.append(list_)
            list_.unwrap()


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

    for table in soup.find_all("table"):
        # TODO: remove the commented draft code
        # for width_elements in soup.find_all(attrs={"width":"yellowbar.png"}):
        # for item in table.find_all():
        #     if item.string is not None:
        #         print(item.string)
        #         item.string = item.string.replace("\n", " ")
        #         print(item.string)
        #         print()
        #     item.attrs.pop("width", None)
        #    item.attrs = {}
        #     if item.name in ("br", "p"):
        #         item.unwrap()
        # for width_element in soup.select('[width]'):
        #     # print(width_element)
        #     del width_element.attrs["width"]
        #     # print(width_element)
        #     # exit()
        # print(table)
        # table.contents = c for c in table.contents
        # table.contents = [
        #     c.replace("\n", " ")
        #     for c in table.contents
        #     if not isinstance(c, str) or c.strip()
        # ]

        # Remove all divs, since they cause pandoc to fail converting the table.
        # https://stackoverflow.com/a/32064299/7410886
        tags_to_remove = ["div", "span"]
        for tag in tags_to_remove:
            for element in table.find_all(tag):
                element.unwrap()

        # another hack: Replace any newlines (<p>, <br>) with a temporary string
        # and with <br> after conversion to markdown.
        for item in table.find_all("br") + table.find_all("p"):
            if item.next_sibling is not None:
                item.append(soup.new_string("{TEMPORARYNEWLINE}"))
            item.unwrap()

        # another hack: handle lists, i. e. replace items with "<br>- ..."
        for item in table.find_all("ul") + table.find_all("ol"):
            item.unwrap()
        for item in table.find_all("li"):
            if item.string is None:
                item.decompose()
                continue
            item.string = "{TEMPORARYNEWLINE}- " + item.string
            item.unwrap()

        for row_index, row in enumerate(table.find_all("tr")):
            for td in row.find_all("td"):
                # tables seem to be headerless always
                # make first row to header
                if row_index == 0:
                    td.name = "th"

        # remove "tbody"
        if (body := table.find("tbody")) is not None:
            body.unwrap()

        table.attrs = {}
