import requests


class JoplinImporter:
    """Import a notebook / note tree and tags to Joplin."""

    def __init__(self, api):
        self.api = api
        self.tag_map = {}

    def import_tags(self, tags):
        # should be called only once at start to avoid tags being created multiple times
        for tag in tags:
            try:
                tag_id = self.api.add_tag(**tag.data)
                self.tag_map[tag.original_id] = tag_id
            except requests.exceptions.HTTPError:
                result = self.api.search(query=tag.data["title"], type="tag")
                matching_tags = [
                    joplin_tag
                    for joplin_tag in result.items
                    if joplin_tag.title == tag.data["title"].lower()
                ]
                assert len(matching_tags) == 1
                self.tag_map[tag.original_id] = matching_tags[0].id

    def import_note(self, note):
        note_id = self.api.add_note(**note.data)
        for tag in note.tags:
            self.api.add_tag_to_note(tag_id=self.tag_map[tag], note_id=note_id)
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
