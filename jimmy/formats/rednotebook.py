"""Convert RedNotebook notes to the intermediate format."""

import datetime
from pathlib import Path
from urllib.parse import urlparse
import re

import yaml

from jimmy import common, converter, intermediate_format as imf
import jimmy.md_lib.convert
import jimmy.md_lib.links


WRONG_QUOTATION_RE = re.compile(r'""(.*?)""\.(.*?)\]')


class Converter(converter.BaseConverter):
    def handle_markdown_links(self, body: str) -> tuple[str, imf.Resources]:
        resources = []
        for link in jimmy.md_lib.links.get_markdown_links(body):
            # Links are usually enclosed with double quotation marks
            # (unparsed text: https://rednotebook.app/help.html#toc37).
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
                resources.append(imf.Resource(Path(link.url), original_link_text, link.text))
        return body, resources

    @common.catch_all_exceptions
    def convert_note(self, data: dict, date: datetime.date):
        title = date.strftime("%Y-%m-%d")
        self.logger.debug(f'Converting note "{title}"')
        # TODO: Could be done with https://pypi.org/project/txt2tags/
        # TODO: links are converted, but not correctly
        # TODO: underline is converted to italic "*"
        # TODO: "standalone" yields errors

        # TODO
        # def fix_quotation_marks(match: re.Match):
        #     return f'""{match.group(1)}.{match.group(2)}""]'
        # body_preprocessed = WRONG_QUOTATION_RE.sub(fix_quotation_marks, data["text"])
        body = self.pandoc.markup_to_markdown(data["text"], format_="t2t", standalone=False)
        body, resources = self.handle_markdown_links(body)
        note_imf = imf.Note(
            title,
            body,
            source_application=self.format,
            resources=resources,
        )
        self.root_notebook.child_notes.append(note_imf)

    def convert(self, file_or_folder: Path):
        notes = list(self.root_path.glob("*.txt"))
        if len(notes) == 0:
            self.logger.warning(
                "Couldn't find a Markdown file. Is this really a Rednotebook export?"
            )
            return

        for file_ in sorted(notes):
            year, month = file_.stem.split("-", 1)
            # data is encapsulated in yaml, notes are in txt2tags markup
            # see: https://rednotebook.app/help.html#toc38
            note_dict = yaml.safe_load(file_.read_text(encoding="utf-8"))
            for day, data in note_dict.items():
                self.convert_note(data, datetime.date(int(year), int(month), int(day)))
