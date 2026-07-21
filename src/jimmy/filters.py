"""Filters for the intermediate format."""

from fnmatch import fnmatchcase

from jimmy import intermediate_format as imf


def select_notes(notebook: imf.Notebook, config):
    """Apply the configured filter to notes in a notebook."""
    selected_child_notes = []
    for child_note in notebook.child_notes:
        title = child_note.title
        tags = [tag.title for tag in child_note.tags]

        # select note by note title
        if config.exclude_notes is not None:
            if not any(fnmatchcase(title, pattern) for pattern in config.exclude_notes):
                selected_child_notes.append(child_note)
        elif config.include_notes is not None:
            if any(fnmatchcase(title, pattern) for pattern in config.include_notes):
                selected_child_notes.append(child_note)

        # select note by tag title
        elif config.exclude_notes_with_tags is not None:
            if not any(
                fnmatchcase(tag_title, pattern)
                for pattern in config.exclude_notes_with_tags
                for tag_title in tags
            ):
                selected_child_notes.append(child_note)
        elif config.include_notes_with_tags is not None:
            if any(
                fnmatchcase(tag_title, pattern)
                for pattern in config.include_notes_with_tags
                for tag_title in tags
            ):
                selected_child_notes.append(child_note)
        else:
            selected_child_notes.append(child_note)

    notebook.child_notes = selected_child_notes


def select_tags(note: imf.Note, config):
    """Apply the configured filter to note tags."""
    selected_tags = []
    for tag in note.tags:
        title = tag.title

        if config.exclude_tags is not None:
            if not any(fnmatchcase(title, pattern) for pattern in config.exclude_tags):
                selected_tags.append(tag)
        elif config.include_tags is not None:
            if any(fnmatchcase(title, pattern) for pattern in config.include_tags):
                selected_tags.append(tag)
        else:
            selected_tags.append(tag)

    note.tags = selected_tags


def apply_filters(root_notebooks: imf.Notebooks, config):
    """
    Apply the configured filter to the complete note tree.
    Filters are mutually exclusive and case sensitive!
    """
    for notebook in root_notebooks:
        apply_filters(notebook.child_notebooks, config)

        select_notes(notebook, config)

        for child_note in notebook.child_notes:
            select_tags(child_note, config)
