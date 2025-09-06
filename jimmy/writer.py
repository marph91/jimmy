"""Convert the intermediate format to Markdown."""

import logging
from pathlib import Path
import re
import shutil
import urllib.parse

from jimmy import common, intermediate_format as imf


LOGGER = logging.getLogger("jimmy")


def get_quoted_relative_path(source: Path, target: Path) -> str:
    """
    >>> get_quoted_relative_path(Path("sample"), Path("sample"))
    '.'
    >>> get_quoted_relative_path(Path("sample/a"), Path("sample/b"))
    '../b'
    >>> get_quoted_relative_path(Path("sample/a"), Path("sample/im age.png"))
    '<../im age.png>'
    """
    # Markdown URLs require posix paths.
    relative_path = str(target.relative_to(source, walk_up=True).as_posix())
    # Prepend "./" for Obsidian compatibility.
    if relative_path != "." and not relative_path.startswith("../"):
        relative_path = f"./{relative_path}"
    # Don't modify the URL if not needed.
    if urllib.parse.quote(relative_path) == relative_path:
        return relative_path
    # Use brackets instead of url encoding to keep cyrillic URLs readable.
    return f"<{relative_path}>"


class PathDeterminer:
    """
    Determine the final paths of notebooks, notes and resources.
    Create a note ID - path map for linking notes in the next pass.
    """

    def __init__(self, config):
        self.root_path = None
        self.max_name_length = config.max_name_length
        self.global_resource_folder = (
            None
            if config.global_resource_folder is None
            else common.safe_path(config.global_resource_folder, self.max_name_length)
        )
        self.local_resource_folder = (
            config.local_resource_folder
            if config.local_resource_folder == Path(".")
            else Path(common.safe_path(config.local_resource_folder, self.max_name_length))
        )
        self.local_image_folder = (
            None
            if config.local_image_folder is None
            else Path(common.safe_path(config.local_image_folder, self.max_name_length))
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
            resource.path = resource_folder / common.safe_path(
                resource.filename.name, self.max_name_length
            )
        else:
            # global resource folder
            resource.path = (
                self.root_path
                / self.global_resource_folder
                / common.safe_path(resource.filename.name, self.max_name_length)
            )
        # add extension if possible
        assert resource.path is not None
        if resource.path.suffix == "":
            if resource.title is not None and (suffix := Path(resource.title).suffix) != "":
                resource.path = resource.path.with_suffix(suffix)
            else:
                guessed_suffix = common.guess_suffix(resource.filename)
                resource.path = resource.path.with_suffix(guessed_suffix)

    def determine_paths(self, notebook: imf.Notebook):
        assert notebook.path is not None
        if self.root_path is None:
            self.root_path = notebook.path
        for note in notebook.child_notes:
            note.path = notebook.path / common.safe_path(note.title, self.max_name_length)
            # Don't overwrite existing suffices.
            if note.path.suffix != ".md":
                note.path = note.path.with_suffix(note.path.suffix + ".md")
            # needed to properly link notes later
            self.note_id_map[note.reference_id] = note.path

            for resource in note.resources:
                self.determine_resource_path(note, resource)
        for child_notebook in notebook.child_notebooks:
            child_notebook.path = notebook.path / common.safe_path(
                child_notebook.title, self.max_name_length
            )
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


class FilesystemWriter:
    """Write notebooks, notes and related data to the filesystem."""

    def __init__(self, note_id_map, stats: common.Stats):
        self.stats = stats
        self.note_id_map: dict[str, Path] = note_id_map

    def update_resource_links(self, note: imf.Note, resource: imf.Resource):
        """Replace the original ID of resources with their path in the filesystem."""
        assert note.path is not None
        assert resource.path is not None
        resource_title = (
            resource.title if resource.title not in [None, ""] else resource.filename.name
        )

        relative_path = get_quoted_relative_path(note.path.parent, resource.path)
        resource_markdown = f"{'!' * resource.is_image}[{resource_title}]({relative_path})"
        if resource.original_text is None:
            # append
            note.body = f"{note.body}\n\n{resource_markdown}"
        else:
            # replace existing link
            # Don't use re.subn(), because the link text may contein invalid characters.
            if (replacement_count := note.body.count(resource.original_text)) == 0:
                # escape first bracket to avoid rich formatting
                resource_text = resource.original_text.replace("[", "\\[")
                LOGGER.warning(
                    f"Made {replacement_count} replacements. "
                    f'Resource link may be corrupted: "{resource_text}".',
                )
            note.body = note.body.replace(resource.original_text, resource_markdown)

    def write_resource(self, resource: imf.Resource):
        # Resolve the source file path to avoid accessing deleted folders, like
        # "deleted_folder/../image.png".
        source_file = resource.filename.resolve()
        if not source_file.exists():
            LOGGER.warning(f'Resource "{source_file}" does not exist.')
            return
        if resource.path is None:
            LOGGER.warning(f'Could not determine path for resource "{source_file}".')
            return

        resource.path = common.get_unique_path(resource.path, source_file)
        # TODO: done for each resource in each note
        resource.path.parent.mkdir(exist_ok=True, parents=True)
        shutil.copy(source_file, resource.path)

    def update_note_links(self, note: imf.Note, note_link: imf.NoteLink):
        """Replace the original ID of notes with their path in the filesystem."""
        assert note.path is not None
        link_title = note_link.title if note_link.title not in [None, ""] else note_link.original_id

        new_path = self.note_id_map.get(note_link.original_id)
        if new_path is None:
            LOGGER.debug(
                f'Note "{note.title}": could not find linked note: "{note_link.original_id}"',
                # prevent [[]] syntax titles to be handled as markup
                extra={"markup": None},
            )
            # Replace at least with the original ID as fallback.
            note.body = note.body.replace(
                note_link.original_text, f"[{link_title}]({note_link.original_id})"
            )
            return

        relative_path = get_quoted_relative_path(note.path.parent, new_path)
        note.body = note.body.replace(note_link.original_text, f"[{link_title}]({relative_path})")

    @common.catch_all_exceptions
    def write_note(self, note: imf.Note):
        # Handle resources and note links first, since the note body changes.
        # "dict.fromkeys()" to remove duplicated resources while retaining order.
        for resource in dict.fromkeys(note.resources):
            # Write resources first before updating the links, since the path
            # can change in case of duplication.
            self.write_resource(resource)
            self.update_resource_links(note, resource)
            self.stats.resources += 1
        for note_link in note.note_links:
            self.update_note_links(note, note_link)
            self.stats.note_links += 1
        # Remove any void links. For example "[](abc)" or "[ ](abc)".
        # This can only be done now to avoid removing any note links or
        # resources unintentionally.
        note.body = remove_void_links(note.body)

        # Finally write the note to the filesystem.
        assert note.path is not None
        note.path = common.get_unique_path(note.path, note.body)
        # We need to unify line endings explicitly. Pathlib converts them later to
        # the OS specific line endings, but only if they are not mixed.
        note.path.write_text(note.body.replace("\r\n", "\n"), encoding="utf-8")
        self.stats.notes += 1  # update stats only after successful write
        self.stats.tags += len(note.tags)

    @common.catch_all_exceptions
    def write_notebook(self, notebook: imf.Notebook):
        assert notebook.path is not None
        notebook.path.mkdir(exist_ok=True, parents=True)
        self.stats.notebooks += 1
        for note in notebook.child_notes:
            self.write_note(note)
        for child_notebook in notebook.child_notebooks:
            self.write_notebook(child_notebook)
        return self.stats
