"""Convert the intermediate format to Joplin notes."""

import logging

import requests

import intermediate_format as imf


LOGGER = logging.getLogger("jimmy")


class JoplinImporter:
    """Import notebooks, notes and related data to Joplin."""

    def __init__(self, api, progress_bars):
        self.api = api
        # Cache created tags and resources to create them only once.
        # original id - joplin id
        self.tag_map: dict[str, imf.Tag] = {}
        # original path - joplin id
        self.resource_map: dict[str, imf.Resource] = {}
        # original id - joplin id
        self.note_id_map: dict[str, str] = {}

        self.progress_bars = progress_bars

    def add_tag(self, tag: imf.Tag) -> str | None:
        self.progress_bars["tags"].update(1)
        try:
            # Try to create a new tag.
            tag_id = self.api.add_tag(**tag.data)
            self.tag_map[tag.reference_id] = tag_id
            return tag_id
        except requests.exceptions.HTTPError:
            # Tag exists already. Search for it. Joplin only supports lower case
            # tags. If not converted to lower case, this can cause some trouble.
            # See: https://github.com/marph91/jimmy/issues/6#issuecomment-2184981456
            title = tag.data["title"].lower()
            result = self.api.search(query=title, type="tag")
            matching_tags = [
                joplin_tag for joplin_tag in result.items if joplin_tag.title == title
            ]
            if len(matching_tags) == 0:
                LOGGER.warning(
                    f'Ignoring tag "{title}". It exists,'
                    "but there aren't search results."
                )
                return None
            if len(matching_tags) > 1:
                LOGGER.warning(
                    f'Too many search results for tag "{title}". '
                    f'Taking first match "{matching_tags[0].id}".'
                )
            self.tag_map[tag.reference_id] = matching_tags[0].id
            return matching_tags[0].id

    def import_note(self, note: imf.Note):
        self.progress_bars["notes"].update(1)
        # Handle resources first, since the note body changes.
        for resource in note.resources:
            self.progress_bars["resources"].update(1)
            resource_title = resource.title or resource.filename.name
            # Don't create multiple Joplin resources for the same file.
            # Cache the original file paths and their corresponding Joplin ID.
            try:
                resource_id = self.resource_map[resource.filename]
            except KeyError:
                resource_id = self.api.add_resource(
                    filename=str(resource.filename), title=resource_title
                )
                self.resource_map[resource.filename] = resource_id
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
            if tag_id is not None:
                self.api.add_tag_to_note(tag_id=tag_id, note_id=note_id)

    def import_notebook(self, notebook: imf.Notebook):
        self.progress_bars["notebooks"].update(1)
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
            self.progress_bars["note_links"].update(1)
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
