"""Convert the intermediate format to Markdown."""

import logging
from pathlib import Path
import re
import shutil
import urllib.parse

import common
import intermediate_format as imf


LOGGER = logging.getLogger("jimmy")


def get_quoted_relative_path(source: Path, target: Path) -> str:
    """
    >>> get_quoted_relative_path(Path("sample"), Path("sample"))
    '.'
    >>> get_quoted_relative_path(Path("sample/a"), Path("sample/b"))
    '../b'
    >>> get_quoted_relative_path(Path("sample/a"), Path("sample/im age.png"))
    '../im%20age.png'
    """
    # TODO: doctest works only on linux. quote seems to be working for windows, though.
    return urllib.parse.quote(str(target.relative_to(source, walk_up=True)))


class PathDeterminer:
    """
    Determine the final paths of notebooks, notes and resources.
    Create a note ID - path map for linking notes in the next pass.
    """

    def __init__(self, config):
        self.root_path = None
        self.global_resource_folder = (
            None
            if config.global_resource_folder is None
            else common.safe_path(config.global_resource_folder)
        )
        self.local_resource_folder = (
            config.local_resource_folder
            if config.local_resource_folder == Path(".")
            else Path(common.safe_path(config.local_resource_folder))
        )
        self.local_image_folder = (
            None
            if config.local_image_folder is None
            else Path(common.safe_path(config.local_image_folder))
        )
        # reference id - path (new id)
        self.note_id_map: dict[str, Path] = {}

    def determine_resource_path(self, note: imf.Note, resource: imf.Resource):
        # determine new resource path
        assert self.root_path is not None
        assert note.path is not None
        if self.global_resource_folder is None:
            if self.local_image_folder is not None and resource.is_image:
                target_folder = self.local_image_folder
            else:
                target_folder = self.local_resource_folder
            # local resources (next to the markdown files)
            resource_folder = note.path.parent / target_folder
            resource.path = resource_folder / common.safe_path(resource.filename.name)
        else:
            # global resource folder
            resource.path = (
                self.root_path
                / self.global_resource_folder
                / common.safe_path(resource.filename.name)
            )
        # add extension if possible
        assert resource.path is not None
        if resource.path.suffix == "":
            if (
                resource.title is not None
                and (suffix := Path(resource.title).suffix) != ""
            ):
                resource.path = resource.path.with_suffix(suffix)
            else:
                guessed_suffix = common.guess_suffix(resource.filename)
                resource.path = resource.path.with_suffix(guessed_suffix)

    def determine_paths(self, notebook: imf.Notebook):
        assert notebook.path is not None
        if self.root_path is None:
            self.root_path = notebook.path
        for note in notebook.child_notes:
            note.path = notebook.path / common.safe_path(note.title)
            # Don't overwrite existing suffices.
            if note.path.suffix != ".md":
                note.path = note.path.with_suffix(note.path.suffix + ".md")
            # needed to properly link notes later
            self.note_id_map[note.reference_id] = note.path

            for resource in note.resources:
                self.determine_resource_path(note, resource)
        for child_notebook in notebook.child_notebooks:
            child_notebook.path = notebook.path / common.safe_path(child_notebook.title)
            self.determine_paths(child_notebook)


VOID_LINK_REGEX = re.compile(r"(?<!!)\[\s*\]\(.*?\)")


def remove_void_links(body: str) -> str:
    """
    Remove void links from Markdown, since they wouldn't be displayed anyway.

    >>> remove_void_links("![](image.png)")
    '![](image.png)'
    >>> remove_void_links("[abc](def)")
    '[abc](def)'
    >>> remove_void_links("[]()")
    ''
    >>> remove_void_links("[](abc)")
    ''
    >>> remove_void_links("[ 	 ](abc)")
    ''
    """

    # sub could be used, but find all is used for logging
    def replace_with_logging(match: re.Match):
        LOGGER.debug(f'Removing void link "{match.group()}"')
        return ""

    return VOID_LINK_REGEX.sub(replace_with_logging, body)


class FilesystemImporter:
    """Import notebooks, notes and related data to the filesystem."""

    def __init__(self, progress_bars, config, stats, note_id_map):
        self.include_title = config.title_as_header
        self.frontmatter = config.frontmatter
        self.progress_bars = progress_bars
        self.note_id_map: dict[str, Path] = note_id_map

        if stats.tags > 0 and not self.frontmatter:
            LOGGER.warning(
                "Tags will be lost without frontmatter. "
                'Frontmatter can be added by "--frontmatter all".'
            )

    def update_resource_links(self, note: imf.Note, resource: imf.Resource):
        """Replace the original ID of resources with their path in the filesystem."""
        assert note.path is not None
        assert resource.path is not None
        resource_title = (
            resource.title
            if resource.title not in [None, ""]
            else resource.filename.name
        )

        relative_path = get_quoted_relative_path(note.path.parent, resource.path)
        resource_markdown = (
            f"{'!' * resource.is_image}[{resource_title}]({relative_path})"
        )
        if resource.original_text is None:
            # append
            note.body = f"{note.body}\n\n{resource_markdown}"
        else:
            # replace existing link
            note.body = note.body.replace(resource.original_text, resource_markdown)

    def write_resource(self, resource: imf.Resource):
        if resource.filename.is_file():
            # Don't create multiple resources for the same file.
            # Cache the original file paths and their corresponding ID.
            # TODO: Check if it's really the same resource or only the same name.
            if resource.path is not None and not resource.path.is_file():
                # TODO: done for each resource in each note
                resource.path.parent.mkdir(exist_ok=True, parents=True)
                shutil.copy(resource.filename, resource.path)
        else:
            LOGGER.warning(f'Resource "{resource.filename}" does not exist.')

    def update_note_links(self, note: imf.Note, note_link: imf.NoteLink):
        """Replace the original ID of notes with their path in the filesystem."""
        assert note.path is not None
        link_title = (
            note_link.title
            if note_link.title not in [None, ""]
            else note_link.original_id
        )

        new_path = self.note_id_map.get(note_link.original_id)
        if new_path is None:
            LOGGER.debug(
                f'Note "{note.title}": '
                f'could not find linked note: "{note_link.original_text}"',
                # prevent [[]] syntax titles to be handled as markup
                extra={"markup": None},
            )
            return

        relative_path = get_quoted_relative_path(note.path.parent, new_path)
        note.body = note.body.replace(
            note_link.original_text, f"[{link_title}]({relative_path})"
        )

    def write_note(self, note: imf.Note):
        self.progress_bars["notes"].update(1)
        if "tags" in self.progress_bars:
            self.progress_bars["tags"].update(len(note.tags))
        assert note.path is not None

        if note.path.is_file():
            # Try to find new name.
            found_new_name = False
            original_path = note.path
            similar_notes = list(
                note.path.parent.glob(f"{note.path.stem}*{note.path.suffix}")
            )
            for new_index in range(1, 10000):
                new_path = (
                    note.path.parent
                    / f"{note.path.stem}_{new_index:04}{note.path.suffix}"
                )
                if new_path not in similar_notes:
                    note.path = new_path
                    found_new_name = True
                    break
            if not found_new_name:
                note.path = (
                    note.path.parent
                    / f"{note.path.stem}_{common.uuid_title()}{note.path.suffix}"
                )
            LOGGER.warning(
                f'Note "{original_path}" exists already. New name: "{note.path.name}"'
            )

        note.path.write_text(
            note.get_finalized_body(self.include_title, self.frontmatter),
            encoding="utf-8",
        )

    @common.catch_all_exceptions
    def import_note(self, note: imf.Note):
        # Handle resources and note links first, since the note body changes.
        for resource in note.resources:
            self.progress_bars["resources"].update(1)
            self.update_resource_links(note, resource)
            self.write_resource(resource)
        for note_link in note.note_links:
            self.progress_bars["note_links"].update(1)
            self.update_note_links(note, note_link)
        # Remove any void links. For example "[](abc)" or "[ ](abc)".
        # This can only be done now to avoid removing any note links or
        # resources unintentionally.
        note.body = remove_void_links(note.body)
        # Finally write the note to the filesystem.
        self.write_note(note)

    @common.catch_all_exceptions
    def import_notebook(self, notebook: imf.Notebook):
        assert notebook.path is not None
        self.progress_bars["notebooks"].update(1)
        notebook.path.mkdir(exist_ok=True, parents=True)
        for note in notebook.child_notes:
            self.import_note(note)
        for child_notebook in notebook.child_notebooks:
            self.import_notebook(child_notebook)
