"""Convert Turtl notes to the intermediate format."""

import json
from pathlib import Path

from jimmy import common, converter, intermediate_format as imf
import jimmy.md_lib.links


class Converter(converter.BaseConverter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # we need a resource folder to avoid writing files to the source folder
        self.resource_folder = common.get_temp_folder()

    def find_parent_notebook(self, space_id, board_id):
        # first level: space
        space = None
        for notebook in self.root_notebook.child_notebooks:
            if notebook.original_id == space_id:
                space = notebook
                break
        if space is None:
            self.logger.debug(f"Couldn't find space with id {space_id}")
            return self.root_notebook

        # second level: board
        if board_id is None:
            return space
        for board in space.child_notebooks:
            if board.original_id == board_id:
                return board
        self.logger.debug(f"Couldn't find board with id {board_id}")
        return self.root_notebook

    def handle_markdown_links(self, body: str, path: Path) -> tuple[imf.Resources, imf.NoteLinks]:
        # pylint: disable=duplicate-code
        # TODO
        note_links = []
        resources = []
        for link in jimmy.md_lib.links.get_markdown_links(body):
            if link.is_web_link or link.is_mail_link:
                continue  # keep the original links
            resource_path = path / link.url
            if resource_path.is_file():
                if common.is_image(resource_path):
                    # resource
                    resources.append(imf.Resource(resource_path, str(link), link.text))
                else:
                    # TODO: this could be a resource, too. How to distinguish?
                    # internal link
                    note_links.append(imf.NoteLink(str(link), Path(link.url).stem, link.text))
        return resources, note_links

    @common.catch_all_exceptions
    def convert_note(self, note: dict, file_map: dict):
        title = note["title"]
        self.logger.debug(f'Converting note "{title}"')
        note_imf = imf.Note(
            title,
            tags=[imf.Tag(t) for t in note["tags"]],
            original_id=note["id"],
            created=common.timestamp_to_datetime(note["mod"]),
            updated=common.timestamp_to_datetime(note["mod"]),
        )
        match note["type"]:
            case "file" | "image" | "link" | "text":
                note_imf.body = note["text"]
            case "password":
                note_imf.body = "\n".join(
                    [
                        f"- Username: `{note['user_id']}`",
                        f"- Password: `{note['password']}`",
                        "",
                        note["text"],
                    ]
                )
            case _:
                self.logger.debug(f'Unhandled type "{note["type"]}"')
        if note.get("url"):
            note_imf.body += f"\n\n<{note['url']}>"

        # note["has_file"] seems to be sometimes wrong...
        # I. e. if the type is "file". Check always.
        # It seems like a note can have maximum one file attached.
        if (file_data := file_map.get(note["id"])) is not None:
            filename = self.resource_folder / note["file"]["name"]
            filename = common.write_base64(filename, file_data)
            file_md = jimmy.md_lib.links.make_link(note["file"]["name"], str(filename))
            note_imf.body += f"\n\n{file_md}"
        # else:
        #     self.logger.debug(f"Couldn't find file with id {note["id"]}")

        resources, note_links = self.handle_markdown_links(note_imf.body, self.resource_folder)
        note_imf.resources = resources
        note_imf.note_links = note_links

        parent_notebook = self.find_parent_notebook(note["space_id"], note["board_id"])
        parent_notebook.child_notes.append(note_imf)

    def convert(self, file_or_folder: Path):
        input_json = json.loads(file_or_folder.read_text(encoding="utf-8"))
        if "notes" not in input_json:
            self.logger.error('"notes" not found. Is this really a Turtl export?')
            return

        for space in input_json["spaces"]:
            self.root_notebook.child_notebooks.append(
                imf.Notebook(space["title"], original_id=space["id"])
            )

        for board in input_json["boards"]:
            for space in self.root_notebook.child_notebooks:
                # TODO: Handle the error case when no space matches.
                if space.original_id == board["space_id"]:
                    space.child_notebooks.append(
                        imf.Notebook(board["title"], original_id=board["id"])
                    )
                    break

        file_map = {}
        for file_ in input_json["files"]:
            # body seems to be empty always
            file_map[file_["id"]] = file_["data"]

        for note in input_json["notes"]:
            self.convert_note(note, file_map)

        # Don't export empty notebooks
        self.remove_empty_notebooks()
