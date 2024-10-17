"""Convert Turtl notes to the intermediate format."""

import base64
from pathlib import Path
import json

import common
import converter
import intermediate_format as imf
import markdown_lib.common


class Converter(converter.BaseConverter):
    accepted_extensions = [".json"]

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

    def handle_markdown_links(
        self, body: str, path: Path
    ) -> tuple[imf.Resources, imf.NoteLinks]:
        # pylint: disable=duplicate-code
        # TODO
        note_links = []
        resources = []
        for link in markdown_lib.common.get_markdown_links(body):
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
                    note_links.append(
                        imf.NoteLink(str(link), Path(link.url).stem, link.text)
                    )
        return resources, note_links

    def convert(self, file_or_folder: Path):
        file_dict = json.loads(file_or_folder.read_text(encoding="utf-8"))

        for space in file_dict["spaces"]:
            self.root_notebook.child_notebooks.append(
                imf.Notebook(space["title"], original_id=space["id"])
            )

        for board in file_dict["boards"]:
            for space in self.root_notebook.child_notebooks:
                # TODO: Handle the error case when no space matches.
                if space.original_id == board["space_id"]:
                    space.child_notebooks.append(
                        imf.Notebook(board["title"], original_id=board["id"])
                    )
                    break

        file_map = {}
        for file_ in file_dict["files"]:
            # body seems to be empty always
            file_map[file_["id"]] = file_["data"]

        for note in file_dict["notes"]:
            note_imf = imf.Note(
                note["title"],
                tags=[imf.Tag(t) for t in note["tags"]],
                original_id=note["id"],
                created=note["mod"],
            )
            match note["type"]:
                case "file" | "image" | "link" | "text":
                    note_imf.body = note["text"]
                case "password":
                    note_imf.body = "\n".join(
                        [
                            f"- Username: `{note["user_id"]}`",
                            f"- Password: `{note["password"]}`",
                            "",
                            note["text"],
                        ]
                    )
                case _:
                    self.logger.debug(f"Unhandled type \"{note["type"]}\"")
            if note.get("url"):
                note_imf.body += f"\n\n<{note["url"]}>"

            # note["has_file"] seems to be sometimes wrong...
            # I. e. if the type is "file". Check always.
            # It seems like a note can have maximum one file attached.
            if (file_data := file_map.get(note["id"])) is not None:
                # TODO: files may be overwritten. use id?
                filename = self.resource_folder / note["file"]["name"]
                filename.write_bytes(base64.b64decode(file_data))
                file_md = f"[{note["file"]["name"]}]({filename})"
                note_imf.body += f"\n\n{file_md}"
            # else:
            #     self.logger.debug(f"Couldn't find file with id {note["id"]}")

            resources, note_links = self.handle_markdown_links(
                note_imf.body, self.resource_folder
            )
            note_imf.resources = resources
            note_imf.note_links = note_links

            parent_notebook = self.find_parent_notebook(
                note["space_id"], note["board_id"]
            )
            parent_notebook.child_notes.append(note_imf)
