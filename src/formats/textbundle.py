"""Convert textbundle or textpack notes to the intermediate format."""

from pathlib import Path
from urllib.parse import unquote

import common
import converter
import intermediate_format as imf


class Converter(converter.BaseConverter):

    def prepare_input(self, input_: Path) -> Path | None:
        match input_.suffix.lower():
            case ".textbundle":
                if not input_.is_dir():
                    self.logger.error("Textbundle should be a folder.")
                    return None
                return input_
            case ".textpack":
                if not input_.is_file():
                    self.logger.error("Textpack should be a file.")
                    return None
                temp_folder = common.extract_zip(input_)
                return common.get_single_child_folder(temp_folder)
            case _:
                self.logger.error("Unsupported format for textbundle")
                return None

    def handle_markdown_links(self, body: str) -> tuple[list, list]:
        resources = []
        for file_prefix, description, url in common.get_markdown_links(body):
            if url.startswith("http"):
                continue  # web link
            if description.startswith("^"):
                continue  # foot note (is working in Joplin without modification)
            original_text = f"{file_prefix}[{description}]({url})"
            # resource
            assert self.root_path is not None
            resource_path = self.root_path / unquote(url)
            if not resource_path.is_file():
                self.logger.warning(f"Couldn't find resource {resource_path}")
                continue
            resources.append(imf.Resource(resource_path, original_text, description))
        return resources, []

    def convert(self, file_or_folder: Path):
        self.root_path = self.prepare_input(file_or_folder)
        if self.root_path is None:
            return

        # TODO: Are internal links and nested folders possible?

        for file_ in self.root_path.iterdir():
            if file_.suffix.lower() not in (".md", ".markdown"):
                # take only the exports in markdown format
                self.logger.debug(f"Ignoring file {file_.name}")
                continue

            markdown = file_.read_text()
            title, body = markdown.split("\n", 1)
            # resources and internal links
            resources, _ = self.handle_markdown_links(body)
            note_joplin = imf.Note(
                {
                    "title": title.lstrip("# "),
                    "body": body.lstrip(),
                    **common.get_ctime_mtime_ms(file_),
                    "source_application": self.format,
                },
                resources=resources,
            )
            self.root_notebook.child_notes.append(note_joplin)
