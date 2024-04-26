"""Convert the intermediate format to Joplin notes."""

import logging

import requests

import intermediate_format as imf


LOGGER = logging.getLogger("joplin_custom_importer")


class JoplinImporter:
    """Import notebooks, notes and related data to Joplin."""

    def __init__(self, api):
        self.api = api
        # Cache created tags to create them only once.
        self.tag_map = {}  # original id - joplin id
        self.note_id_map = {}  # original id - joplin id

    def add_tag(self, tag: imf.Tag) -> str:
        try:
            tag_id = self.api.add_tag(**tag.data)
            self.tag_map[tag.reference_id] = tag_id
            return tag_id
        except requests.exceptions.HTTPError:
            # Tag exists already. Search for it.
            result = self.api.search(query=tag.data["title"], type="tag")
            matching_tags = [
                joplin_tag
                for joplin_tag in result.items
                if joplin_tag.title == tag.data["title"].lower()
            ]
            assert len(matching_tags) == 1
            self.tag_map[tag.reference_id] = matching_tags[0].id
            return matching_tags[0].id

    def import_note(self, note: imf.Note):
        # Handle resources first, since the note body changes.
        for resource in note.resources:
            resource_title = resource.title or resource.filename.name
            resource_id = self.api.add_resource(
                filename=str(resource.filename), title=resource_title
            )
            resource_markdown = (
                f"{'!' * resource.is_image}[{resource_title}](:/{resource_id})"
            )
            if resource.original_text is None:
                # append
                note.data["body"] = f"{note.data.get('body', '')}\n{resource_markdown}"
            else:
                # replace existing link
                note.data["body"] = note.data["body"].replace(
                    resource.original_text, resource_markdown
                )

        note_id = self.api.add_note(**note.data)
        # needed to properly link notes later
        note.joplin_id = note_id
        self.note_id_map[note.reference_id] = note_id

        for tag in note.tags:
            tag_id = self.tag_map.get(tag.reference_id, self.add_tag(tag))
            self.api.add_tag_to_note(tag_id=tag_id, note_id=note_id)

    def import_notebook(self, notebook: imf.Notebook):
        notebook_id = self.api.add_notebook(**notebook.data)
        for note in notebook.child_notes:
            note.data["parent_id"] = notebook_id
            self.import_note(note)
        for child_notebook in notebook.child_notebooks:
            child_notebook.data["parent_id"] = notebook_id
            self.import_notebook(child_notebook)

    def update_note_links(self, note: imf.Note):
        if not note.note_links or not note.data.get("body", ""):
            return  # nothing to link
        for note_link in note.note_links:
            joplin_id = self.note_id_map.get(note_link.original_id)
            if joplin_id is None:
                LOGGER.debug(f"Couldn't find matching note: {note_link.original_text}")
            note.data["body"] = note.data["body"].replace(
                note_link.original_text, f"[{note_link.title}](:/{joplin_id})"
            )
        self.api.modify_note(note.joplin_id, body=note.data["body"])

    def link_notes(self, notebook: imf.Notebook):
        for note in notebook.child_notes:
            self.update_note_links(note)
        for child_notebook in notebook.child_notebooks:
            self.link_notes(child_notebook)
