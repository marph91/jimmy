"""Convert the intermediate format to Joplin notes."""

import requests

from intermediate_format import Tag


class JoplinImporter:
    """Import a notebook / note tree and tags to Joplin."""

    def __init__(self, api):
        self.api = api
        # Cache created tags to create them only once.
        self.tag_map = {}  # original id - joplin id

    def add_tag(self, tag: Tag) -> str:
        try:
            tag_id = self.api.add_tag(**tag.data)
            self.tag_map[tag.original_id] = tag_id
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
            self.tag_map[tag.original_id] = matching_tags[0].id
            return matching_tags[0].id

    def import_note(self, note):
        note_id = self.api.add_note(**note.data)
        for tag in note.tags:
            tag_id = self.tag_map.get(tag.original_id, self.add_tag(tag))
            self.api.add_tag_to_note(tag_id=tag_id, note_id=note_id)
        for resource in note.resources:
            resource_id = self.api.add_resource(
                filename=str(resource), title=resource.name
            )
            self.api.add_resource_to_note(resource_id=resource_id, note_id=note_id)

    def import_notebook(self, notebook):
        notebook_id = self.api.add_notebook(**notebook.data)
        for note in notebook.child_notes:
            note.data["parent_id"] = notebook_id
            self.import_note(note)
        for child_notebook in notebook.child_notebooks:
            child_notebook.data["parent_id"] = notebook_id
            self.import_notebook(child_notebook)
