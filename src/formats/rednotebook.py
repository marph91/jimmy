"""Convert RedNotebook notes to the intermediate format."""

from pathlib import Path
from urllib.parse import urlparse

import yaml

import common
import converter
import intermediate_format as imf


class Converter(converter.BaseConverter):
    accepted_extensions = [".zip"]
    accept_folder = True

    def prepare_input(self, input_: Path) -> Path:
        match input_.suffix.lower():
            case ".zip":
                return common.extract_zip(input_)
            case _:  # data folder:
                return input_

    def handle_markdown_links(self, body: str) -> tuple[str, list]:
        resources = []
        for link in common.get_markdown_links(body):
            # Links are usually enclosed with double quotation marks.
            # They get removed in some cases when parsing. Add them again
            # to get the original string.
            if not link.url.startswith('""'):
                link.url = f'""{link.url}""'
            original_link_text = str(link)

            # remove double quotation marks
            link.url = link.url.replace('""', "")
            # remove the "file://" protocol if needed
            parsed_link = urlparse(link.url)
            if parsed_link.scheme == "file":
                link.url = parsed_link.path

            if link.is_web_link or link.is_mail_link:
                # Resource links get replaced later,
                # but these links need to be replaced here.
                body = body.replace(f'""{link.url}""', link.url)
            else:
                # resource
                if link.url is None:
                    continue
                resources.append(
                    imf.Resource(Path(link.url), original_link_text, link.text)
                )
        return body, resources

    def convert(self, file_or_folder: Path):
        self.root_path = self.prepare_input(file_or_folder)

        for file_ in self.root_path.glob("*.txt"):
            # TODO: Split year into separate notebook?
            parent_notebook = imf.Notebook({"title": file_.stem})
            self.root_notebook.child_notebooks.append(parent_notebook)

            # data is encapsulated in yaml, notes are in txt2tags markup
            # see: https://rednotebook.app/help.html#toc38
            note_dict = yaml.safe_load(file_.read_text())
            for day, data in note_dict.items():
                # TODO: Could be done with https://pypi.org/project/txt2tags/
                # TODO: links are converted, but not correctly
                body = common.markup_to_markdown(data["text"], format_="t2t")
                body, resources = self.handle_markdown_links(body)
                note_imf = imf.Note(
                    {
                        "title": str(day),
                        "body": body,
                        "source_application": self.format,
                    },
                    resources=resources,
                )
                parent_notebook.child_notes.append(note_imf)
