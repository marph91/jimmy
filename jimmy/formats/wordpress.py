"""Convert a Wordpress XML export to the intermediate format."""

from pathlib import Path
import xml.etree.ElementTree as ET  # noqa: N817

from jimmy import common, converter, intermediate_format as imf
import jimmy.md_lib.common


def get_text(element, default: str | None = None) -> str | None:
    if element is not None and element.text is not None:
        return element.text
    return default


class Converter(converter.BaseConverter):
    @common.catch_all_exceptions
    def convert_note(self, item, parent_notebook: imf.Notebook, namespaces):
        title = get_text(item.find("title"), default=common.unique_title())
        if (post_type := get_text(item.find("wp:post_type", namespaces))) in (
            "nav_menu_item",
            "wp_global_styles",
            "wp_navigation",
        ):
            self.logger.debug(f'Skipping {post_type} "{title}"')
            return
        self.logger.debug(f'Converting note "{title}"')
        assert title is not None
        note_imf = imf.Note(title)

        # TODO: note links
        # TODO: hierarchy: post_id - post_parent
        note_imf.original_id = get_text(item.find("guid"))

        if bool(int(get_text(item.find("wp:is_sticky", namespaces)))):  # type:ignore[arg-type]
            note_imf.tags.append(imf.Tag("sticky"))
        note_imf.tags.extend(
            [
                imf.Tag(category.text)
                for category in item.findall("category")
                if category.text is not None
            ]
        )
        note_imf.author = get_text(item.find("dc:creator", namespaces))

        try:
            note_imf.created = common.iso_to_datetime(
                get_text(item.find("wp:post_date_gmt", namespaces))  # type:ignore[arg-type]
            )
            note_imf.updated = common.iso_to_datetime(
                get_text(item.find("wp:post_modified_gmt", namespaces))  # type:ignore[arg-type]
            )
        except (TypeError, ValueError):
            self.logger.debug("Failed to parse date.")

        content = get_text(item.find("content:encoded", namespaces))
        if content is not None:
            note_imf.body = jimmy.md_lib.common.markup_to_markdown(content)
        for attachment in item.findall("wp:attachment_url", namespaces):
            attachment_text = get_text(attachment)
            if attachment_text is None:
                continue
            if attachment_text.lower().endswith((".gif", ".png", ".jpg", ".jpeg", ".webp")):
                attchment_md = f"![]({attachment_text})\n"
            else:
                attchment_md = f"<{attachment_text}>\n"
            note_imf.body += attchment_md

        if comments := item.findall("wp:comment", namespaces):
            comments_md = ["", "", "## Comments"]
            for comment in comments:
                comment_author = get_text(
                    comment.find("wp:comment_author", namespaces),
                    default="Unknown",
                )
                comment_content = get_text(comment.find("wp:comment_content", namespaces))
                if comment_content is not None:
                    comment_content_md = jimmy.md_lib.common.markup_to_markdown(
                        comment_content, standalone=False
                    )
                    comments_md.extend(["", f"**{comment_author}**: {comment_content_md}"])
            note_imf.body += "\n".join(comments_md)

        parent_notebook.child_notes.append(note_imf)

    @common.catch_all_exceptions
    def convert(self, file_or_folder: Path):
        # first pass: parse namespaces
        # TODO: move to common
        namespaces = {
            node[0]: node[1] for _, node in ET.iterparse(file_or_folder, events=["start-ns"])
        }

        # second pass: actual conversion
        root_node = ET.parse(file_or_folder).getroot()
        for channel in root_node.findall("channel"):
            title = get_text(channel.find("title"), default=common.unique_title())
            assert title is not None
            self.logger.debug(f'Converting notebook "{title}"')
            parent_notebook = imf.Notebook(title)
            self.root_notebook.child_notebooks.append(parent_notebook)

            for item in channel.findall("item"):
                self.convert_note(item, parent_notebook, namespaces)
