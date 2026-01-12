"""Convert nimbus notes to the intermediate format."""

from pathlib import Path
from urllib.parse import unquote

from bs4 import BeautifulSoup

from jimmy import common, converter, intermediate_format as imf
import jimmy.md_lib.convert
import jimmy.md_lib.html_filter
import jimmy.md_lib.links


class Converter(converter.BaseConverter):
    def __init__(self, config: common.Config):
        super().__init__(config)
        self._input_note_index = 0
        self.temp_folder = common.get_temp_folder()
        self.note_title_map: dict[str, str] = {}

    def handle_markdown_links(
        self, note_body: str, root_folder: Path
    ) -> tuple[str, imf.Resources, imf.NoteLinks]:
        note_links = []
        resources = []
        for link in jimmy.md_lib.links.get_markdown_links(note_body):
            if link.is_web_link or link.is_mail_link:
                continue  # keep the original links
            # speciality of nimbus note: duplicated https
            if link.url.startswith("https:https://"):
                note_body = note_body.replace(link.url, link.url[len("https:") :])
                continue
            if "nimbusweb.me" in link.url:
                # internal link
                # TODO: Get export file with internal links.
                self.logger.debug(f"Skip internal link {link.url}, because there is no test data.")
            elif link.url.startswith("nimbusnote://"):
                linked_note_name = unquote(link.url[len("nimbusnote://") :])
                note_links.append(
                    imf.NoteLink(str(link), linked_note_name, link.text or linked_note_name)
                )
            elif link.url.startswith("#"):
                continue  # internal link to heading
            elif (root_folder / link.url).is_file():
                # resource
                resources.append(imf.Resource(root_folder / link.url, str(link), link.text))
            elif link.url.startswith("data:image/svg+xml;base64,"):
                # TODO: Generalize for other mime types.
                # For example "data:image/png;base64,"
                base64_data = link.url[len("data:image/svg+xml;base64,") :]
                original_name = link.text
                temp_filename = root_folder / (original_name or common.unique_title())
                temp_filename = common.write_base64(temp_filename, base64_data)
                resources.append(
                    imf.Resource(
                        temp_filename,
                        jimmy.md_lib.links.make_link(link.text, link.url, is_image=link.is_image),
                        temp_filename.name,
                    )
                )
            elif (
                other_resource_path := common.try_other_suffixes(root_folder / link.url)
            ) is not None:
                # last resort: sometimes the extension is changed and referenced incorrectly
                resources.append(imf.Resource(other_resource_path, str(link), link.text))
            else:
                self.logger.warning(f'Resource "{root_folder / link.url}" does not exist.')

        return note_body, resources, note_links

    @common.catch_all_exceptions
    def convert_note(self, file_: Path, parent: imf.Notebook):
        self.logger.debug(f'Converting note {self._input_note_index + 1} "{file_.stem}"')
        # Use a simple index to avoid folder name issues on Windows.
        temp_folder_note = self.temp_folder / str(self._input_note_index)
        temp_folder_note.mkdir()
        self._input_note_index += 1
        common.extract_zip(file_, temp_folder=temp_folder_note)

        if not (temp_folder_note / "note.html").is_file():
            self.logger.error("Export structure not implemented yet. Please report at Github.")
            return

        if not (temp_folder_note / "assets").is_dir():
            self.logger.warning('"assets" folder not found. Resources might be missing.')

        # HTML note seems to have the name "note.html" always
        note_html = (temp_folder_note / "note.html").read_text(encoding="utf-8")

        # Use the filename only as fallback title,
        # because some characters might be replaced.
        # TODO: soup is created for filtering again
        soup = BeautifulSoup(note_html, "html.parser")
        if (title_element := soup.find("title")) is not None and title_element.text:
            title = title_element.text
        else:
            title = file_.stem
        self.note_title_map[title] = title

        note_imf = imf.Note(title, source_application=self.format, original_id=title)

        note_imf.body = jimmy.md_lib.convert.markup_to_markdown(
            note_html,
            pwd=temp_folder_note,
            custom_filter=[
                jimmy.md_lib.html_filter.nimbus_note_add_mark,
                jimmy.md_lib.html_filter.nimbus_note_add_note_links,
                jimmy.md_lib.html_filter.nimbus_note_streamline_lists,
                jimmy.md_lib.html_filter.nimbus_note_streamline_tables,
                jimmy.md_lib.html_filter.nimbus_strip_images,
            ],
        ).strip()
        note_imf.body, note_imf.resources, note_imf.note_links = self.handle_markdown_links(
            note_imf.body, temp_folder_note
        )

        # append unreferenced resources
        linked_resource_names = [r.filename.name for r in note_imf.resources]
        if (temp_folder_note / "assets").is_dir():
            for resource in (temp_folder_note / "assets").iterdir():
                if resource.is_dir() or resource.name == "theme.css":
                    continue
                if resource.name not in linked_resource_names:
                    note_imf.resources.append(imf.Resource(resource))

        parent.child_notes.append(note_imf)

    def convert_folder(self, file_or_folder: Path, parent: imf.Notebook):
        for item in sorted(file_or_folder.iterdir()):
            if item.is_dir():
                new_parent = imf.Notebook(item.name)
                self.convert_folder(item, new_parent)
                parent.child_notebooks.append(new_parent)
            elif item.suffix == ".zip":
                self.convert_note(item, parent)

    def improve_note_links(self):
        for note in self.root_notebook.get_all_child_notes():
            for note_link in note.note_links:
                best_match_id = common.get_best_match(note_link.original_id, self.note_title_map)
                if best_match_id is not None:
                    note_link.original_id = best_match_id

    def convert(self, file_or_folder: Path):
        if file_or_folder.suffix == ".zip":
            self.convert_note(file_or_folder, self.root_notebook)
        else:  # folder of .zip
            self.convert_folder(file_or_folder, self.root_notebook)

        # second pass: fix odd note links
        self.improve_note_links()

        # Don't export empty notebooks
        self.remove_empty_notebooks()
