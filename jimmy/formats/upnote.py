"""Convert UpNote notes to the intermediate format."""

import json
from pathlib import Path
import urllib.parse

from jimmy import common, converter, intermediate_format as imf
import jimmy.md_lib.common
import jimmy.md_lib.html_filter


class Converter(converter.BaseConverter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_id_name_map = {}
        self.notebook_id_map = {}
        self.note_id_notebook_id_map = {}
        self.tag_id_map = {}

    def handle_markdown_links(
        self, note_body: str, resource_folder: Path
    ) -> tuple[str, imf.Resources, imf.NoteLinks, imf.Tags]:
        note_links = []
        resources = []
        tags = []
        for link in jimmy.md_lib.common.get_markdown_links(note_body):
            if link.url.startswith("http://localhost"):
                # resource
                if resource_folder.is_dir():
                    filename = Path(urllib.parse.urlparse(link.url).path).name
                    # TODO: Sometimes upnote uses the id. Try to resolve the filename.
                    # if (new_filename := self.file_id_name_map.get(filename)):
                    #     filename = new_filename
                    resources.append(imf.Resource(resource_folder / filename, str(link), link.text))
                continue
            if link.is_web_link or link.is_mail_link:
                continue  # keep the original links
            if link.url.startswith("upnote://x-callback-url/openNote?noteId="):
                # note link
                linked_note_id = link.url[len("upnote://x-callback-url/openNote?noteId=") :]
                note_links.append(imf.NoteLink(str(link), linked_note_id, link.text))
            elif link.url.startswith("upnote://x-callback-url/tag/view?tag="):
                # tag
                note_body = note_body.replace(str(link), link.text)
                tags.append(imf.Tag(link.text.lstrip("#")))
        return note_body, resources, note_links, tags

    @common.catch_all_exceptions
    def convert_note(self, note_upnote: dict, resource_path: Path):
        title = note_upnote["data"]["title"]
        self.logger.debug(f'Converting note "{title}"')

        if note_upnote["data"].get("trashed", False) or note_upnote["data"].get("deleted", False):
            self.logger.debug("Skipping trashed or deleted note.")
            return

        if note_upnote["data"].get("isTemplate", False):
            self.logger.debug("Skipping template.")
            return

        id_ = note_upnote["data"]["id"]
        note_imf = imf.Note(
            title,
            created=common.timestamp_to_datetime(note_upnote["data"]["createdAt"] // 10**3),
            updated=common.timestamp_to_datetime(note_upnote["data"]["updatedAt"] // 10**3),
            original_id=id_,
            source_application=self.format,
        )

        note_body = jimmy.md_lib.common.markup_to_markdown(
            note_upnote["data"]["html"],
            custom_filter=[
                jimmy.md_lib.html_filter.upnote_add_formula,
                jimmy.md_lib.html_filter.upnote_add_highlight,
                jimmy.md_lib.html_filter.upnote_streamline_checklists,
            ],
        )

        # TODO: Are there only inline tags?
        note_imf.body, note_imf.resources, note_imf.note_links, note_imf.tags = (
            self.handle_markdown_links(note_body, resource_path)
        )

        # special tags
        for tag_name in ("bookmarked", "pinned", "trashed", "deleted", "highlighted"):
            if note_upnote["data"].get(tag_name, False):
                note_imf.tags.append(imf.Tag(f"upnote-{tag_name}"))

        # determine parent notebook
        if (parent_notebook_id := self.note_id_notebook_id_map.get(id_)) is None:
            self.logger.warning(f"Note ID not found ({id_}). Adding note to root notebook.")
            parent_notebook = self.root_notebook
        elif (potential_parent_notebook := self.notebook_id_map.get(parent_notebook_id)) is None:
            self.logger.warning(
                f"Parent notebook ID not found ({parent_notebook_id}). "
                "Adding note to root notebook."
            )
            parent_notebook = self.root_notebook
        else:
            parent_notebook = potential_parent_notebook
        parent_notebook.child_notes.append(note_imf)

    def convert_backup(self, backup_file: Path):
        self.logger.info(f'Selected backup file "{backup_file}"')
        resource_folder = backup_file.parent / ".." / "files"
        if not resource_folder.is_dir():
            self.logger.warning(
                f'Could not find resource folder at "{resource_folder}". '
                "Resources won't be converted."
            )

        backup_file = common.extract_gzip(backup_file)
        backup_text = backup_file.read_text(encoding="utf-8")
        backup_lines = backup_text.split("\n")
        if backup_lines[0] != "version:2":
            self.logger.warning(f"Unsupported version {backup_lines[0]}")

        backup_dicts = [json.loads(backup_line) for backup_line in backup_lines[1:]]

        # first iteration parse all notebooks and tags
        for backup_dict in backup_dicts:
            match backup_dict["type"]:
                case "files":
                    # example ID: '2e80e4b0-f9e4-49f8-a6ac-4c3051f208fe__png'
                    file_id = backup_dict["data"]["id"].replace("__", ".")
                    file_name = backup_dict["data"]["name"]
                    self.file_id_name_map[file_id] = file_name
                case "notebooks":
                    id_ = backup_dict["data"]["id"]
                    notebook_imf = imf.Notebook(
                        backup_dict["data"]["title"],
                        created=backup_dict["data"]["createdAt"],
                        updated=backup_dict["data"]["updatedAt"],
                        original_id=id_,
                    )
                    self.notebook_id_map[id_] = notebook_imf
                case "lists":
                    if (id_ := backup_dict["data"]["id"]).startswith("notebooks_"):
                        # 1 notebook to N notes mapping
                        notebook_id = id_[len("notebooks_") :]
                        # note IDs are json encoded
                        for note_id in json.loads(backup_dict["data"]["content"]):
                            self.note_id_notebook_id_map[note_id] = notebook_id
                case "organizers":
                    # 1 notebook to 1 note mapping
                    note_id = backup_dict["data"]["noteId"]
                    notebook_id = backup_dict["data"]["notebookId"]
                    self.note_id_notebook_id_map[note_id] = notebook_id
                case "tags":
                    id_ = backup_dict["data"]["id"]
                    self.tag_id_map[id_] = imf.Tag(backup_dict["data"]["title"])

        # second iteration create hierarchy including notes and notebooks
        for backup_dict in backup_dicts:
            match backup_dict["type"]:
                case "notebooks":
                    id_ = backup_dict["data"]["id"]
                    if (parent_notebook_id := backup_dict["data"]["parent"]) in ("", None):
                        parent_notebook = self.root_notebook
                    else:
                        parent_notebook = self.notebook_id_map[parent_notebook_id]
                    parent_notebook.child_notebooks.append(self.notebook_id_map[id_])
                case "filters" | "files" | "lists" | "organizers" | "tags":
                    pass  # handled already or unused
                case "notes":
                    self.convert_note(backup_dict, resource_folder)
                case _:
                    self.logger.debug(f'Skipping unexpected key "{backup_dict["type"]}".')

    def convert(self, file_or_folder: Path):
        backup_files = list(file_or_folder.rglob("*.upnx"))
        if len(backup_files) == 0:
            self.logger.warning(
                f"Couldn't find a .upnx backup file at {backup_files}. "
                "Is this the correct location of the UpNote backup?"
            )
            return
        # take the latest backup
        self.convert_backup(sorted(backup_files)[-1])
