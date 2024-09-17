"""Convert the intermediate format to markdown."""

import logging
import os.path
from pathlib import Path
import shutil
import urllib.parse

import frontmatter

import intermediate_format as imf


LOGGER = logging.getLogger("jimmy")


class FilesystemImporter:
    """Import notebooks, notes and related data to the filesystem."""

    def __init__(self, progress_bars, frontmatter_):
        self.frontmatter = frontmatter_
        # reference id - path (new id)
        self.note_id_map: dict[str, Path] = {}
        self.progress_bars = progress_bars

    def write_note(self, note: imf.Note):
        assert note.path is not None
        match self.frontmatter:
            case "joplin":
                # TODO
                # https://joplinapp.org/help/dev/spec/interop_with_frontmatter/
                metadata = {"title": note.data["title"]}
                if note.tags:
                    metadata["tags"] = [tag.data["title"] for tag in note.tags]
                key_map = {
                    "user_created_time": "created",
                    "user_updated_time": "updated",
                    "author": "author",
                    "latitude": "latitude",
                    "longitude": "longitude",
                    "altitude": "altitude",
                }
                for original_key, mapped_key in key_map.items():
                    if value := note.data.get(original_key):
                        metadata[mapped_key] = value
                if note.data.get("is_todo", False):
                    metadata["completed?"] = (
                        "yes" if note.data["todo_completed"] else "no"
                    )
                    if note.data["todo_due"] != 0:
                        metadata["due"] = note.data["todo_due"]
                post = frontmatter.Post(note.data.get("body", ""), **metadata)
                frontmatter.dump(post, note.path)
            case "obsidian":
                # https://help.obsidian.md/Editing+and+formatting/Properties#Property+format
                metadata = {}
                if note.tags:
                    metadata["tags"] = [tag.data["title"] for tag in note.tags]
                    post = frontmatter.Post(note.data.get("body", ""), **metadata)
                    frontmatter.dump(post, note.path)
                else:
                    note.path.write_text(note.data.get("body", ""))
            case _:
                note.path.write_text(note.data.get("body", ""))

    def import_note(self, note: imf.Note):
        assert note.path is not None
        self.progress_bars["notes"].update(1)
        # Handle resources first, since the note body changes.
        for resource in note.resources:
            self.progress_bars["resources"].update(1)
            resource_title = resource.title or resource.filename.name
            # TODO: support local and global resource folder
            resource.path = note.path.parent / resource.filename.name
            # Don't create multiple Joplin resources for the same file.
            # Cache the original file paths and their corresponding Joplin ID.
            if not resource.path.is_file():
                shutil.copy(resource.filename, resource.path)
            resource_markdown = (
                f"{'!' * resource.is_image}[{resource_title}]({resource.path.name})"
            )
            if resource.original_text is None:
                # append
                note.data["body"] = f"{note.data.get('body', '')}\n{resource_markdown}"
            else:
                # replace existing link
                note.data["body"] = note.data["body"].replace(
                    resource.original_text, resource_markdown
                )

        # needed to properly link notes later
        self.note_id_map[note.reference_id] = note.path

        if len(note.tags) > 0:
            self.progress_bars["tags"].update(len(note.tags))
            if not self.frontmatter:
                LOGGER.warning(
                    f"Tags of note \"{note.data['title']}\" "
                    "will be lost without frontmatter."
                )
        self.write_note(note)

    def import_notebook(self, notebook: imf.Notebook):
        assert notebook.path is not None
        self.progress_bars["notebooks"].update(1)
        notebook.path.mkdir(exist_ok=True, parents=True)  # TODO
        for note in notebook.child_notes:
            note.path = (notebook.path / note.data["title"]).with_suffix(".md")
            self.import_note(note)
        for child_notebook in notebook.child_notebooks:
            child_notebook.path = notebook.path / child_notebook.data["title"]
            self.import_notebook(child_notebook)

    def update_note_links(self, note: imf.Note):
        assert note.path is not None
        if not note.note_links or not note.data.get("body", ""):
            return  # nothing to link
        for note_link in note.note_links:
            self.progress_bars["note_links"].update(1)
            new_path = self.note_id_map.get(note_link.original_id)
            if new_path is None:
                LOGGER.debug(f"Couldn't find matching note: {note_link.original_text}")
                continue

            relative_path = os.path.relpath(
                new_path.resolve(), start=note.path.parent.resolve()
            )
            note.data["body"] = note.data["body"].replace(
                note_link.original_text,
                f"[{note_link.title}]({urllib.parse.quote(str(relative_path))})",
            )
        self.write_note(note)  # update note

    def link_notes(self, notebook: imf.Notebook):
        for note in notebook.child_notes:
            self.update_note_links(note)
        for child_notebook in notebook.child_notebooks:
            self.link_notes(child_notebook)
