"""Convert RedNotebook notes to the intermediate format."""

from pathlib import Path
from urllib.parse import urlparse

import yaml

import common
import converter
import intermediate_format as imf
import markdown_lib


class Converter(converter.BaseConverter):
    accepted_extensions = [".zip"]
    accept_folder = True

    def handle_markdown_links(self, body: str) -> tuple[str, imf.Resources]:
        resources = []
        for link in markdown_lib.common.get_markdown_links(body):
            # Links are usually enclosed with double quotation marks.
            # They get removed in some cases when parsing. Add them again
            # to get the original string.
            if not link.url.startswith("%22%22"):
                link.url = f"%22%22{link.url}%22%22"
            original_link_text = str(link)

            # remove double quotation marks
            link.url = link.url.replace("%22%22", "")
            # remove the "file://" protocol if needed
            parsed_link = urlparse(link.url)
            if parsed_link.scheme == "file":
                link.url = parsed_link.path

            if link.is_web_link or link.is_mail_link:
                # Resource links get replaced later,
                # but these links need to be replaced here.
                body = body.replace(f"%22%22{link.url}%22%22", link.url)
            else:
                # resource
                if link.url is None:
                    continue
                resources.append(
                    imf.Resource(Path(link.url), original_link_text, link.text)
                )
        return body, resources

    @common.catch_all_exceptions
    def convert_note(self, data: dict, day, parent_notebook: imf.Notebook):
        self.logger.debug(f'Converting note "{day}"')
        # TODO: Could be done with https://pypi.org/project/txt2tags/
        # TODO: links are converted, but not correctly
        body = markdown_lib.common.markup_to_markdown(data["text"], format_="t2t")
        body, resources = self.handle_markdown_links(body)
        note_imf = imf.Note(
            str(day),
            body,
            source_application=self.format,
            resources=resources,
        )
        parent_notebook.child_notes.append(note_imf)

    def convert(self, file_or_folder: Path):
        for file_ in sorted(self.root_path.glob("*.txt")):
            # TODO: Split year into separate notebook?
            parent_notebook = imf.Notebook(file_.stem)
            self.root_notebook.child_notebooks.append(parent_notebook)

            # data is encapsulated in yaml, notes are in txt2tags markup
            # see: https://rednotebook.app/help.html#toc38
            note_dict = yaml.safe_load(file_.read_text(encoding="utf-8"))
            for day, data in note_dict.items():
                self.convert_note(data, day, parent_notebook)
