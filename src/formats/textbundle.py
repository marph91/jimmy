"""Convert textbundle or textpack notes to the intermediate format."""

from pathlib import Path
from urllib.parse import unquote

import common
import converter
import intermediate_format as imf


class Converter(converter.BaseConverter):
    accepted_extensions = [".textbundle", ".textpack"]

    def prepare_input(self, input_: Path) -> Path:
        match input_.suffix.lower():
            case ".textbundle":
                return input_
            case _:  # ".textpack":
                temp_folder = common.extract_zip(input_)
                return common.get_single_child_folder(temp_folder)

    def handle_markdown_links(self, body: str) -> tuple[list, list]:
        resources = []
        for link in common.get_markdown_links(body):
            if link.is_web_link or link.is_mail_link:
                continue  # keep the original links
            if link.text.startswith("^"):
                continue  # foot note (is working in Joplin without modification)
            # resource
            assert self.root_path is not None
            resource_path = self.root_path / unquote(link.url)
            if not resource_path.is_file():
                self.logger.warning(f"Couldn't find resource {resource_path}")
                continue
            resources.append(imf.Resource(resource_path, str(link), link.text))
        return resources, []

    def convert(self, file_or_folder: Path):
        self.root_path = self.prepare_input(file_or_folder)

        # TODO: Are internal links and nested folders supported by this format?

        for file_ in self.root_path.iterdir():
            if file_.suffix.lower() not in (".md", ".markdown"):
                # take only the exports in markdown format
                self.logger.debug(f"Ignoring file {file_.name}")
                continue

            title, body = common.split_h1_title_from_body(
                file_.read_text(encoding="utf-8")
            )
            inline_tags = common.get_inline_tags(body, ["#"])
            resources, _ = self.handle_markdown_links(body)
            note_imf = imf.Note(
                **{
                    "title": title,
                    "body": body,
                    **common.get_ctime_mtime_ms(file_),
                    "source_application": self.format,
                },
                tags=[imf.Tag(tag) for tag in inline_tags],
                resources=resources,
            )
            self.root_notebook.child_notes.append(note_imf)
