"""Convert the intermediate format to Markdown."""

import dataclasses
import logging
from pathlib import Path
import re
import shutil
import urllib.parse

import frontmatter

import common
import intermediate_format as imf


LOGGER = logging.getLogger("jimmy")


def safe_path(path: Path | str, max_name_length: int = 50) -> Path | str:
    r"""
    Return a safe version of the provided path or string.
    Only the last part is considered if a path is provided.

    >>> str(safe_path(Path("a/.")))
    'a'
    >>> str(safe_path(Path("ab\x00c")))
    'ab_c'
    >>> str(safe_path(Path("CON")))
    'CON_'
    >>> str(safe_path(Path("LPT7")))
    'LPT7_'
    >>> str(safe_path(Path("bc.")))
    'bc_'
    >>> safe_path("b:c")
    'b_c'
    >>> str(safe_path(Path("b*c")))
    'b_c'
    >>> safe_path("a/b/c")
    'a_b_c'
    >>> safe_path("")  # doctest:+ELLIPSIS
    'unnamed_...'
    >>> safe_path("g" * 50, max_name_length=4)
    'gggg'
    """
    safe_name = path if isinstance(path, str) else path.name
    if safe_name == "":
        return common.unique_title()

    # https://stackoverflow.com/a/31976060
    # Windows restrictions
    # fmt: off
    forbidden_chars = [
        "<", ">", ":", "\"", "/", "\\", "|", "?", "*",
    ] + [chr(value) for value in range(32)]
    # fmt: on
    for char in forbidden_chars:
        safe_name = safe_name.replace(char, "_")

    forbidden_names = (
        ["CON", "PRN", "AUX", "NUL"]
        + [f"COM{i}" for i in range(1, 10)]
        + [f"LPT{i}" for i in range(1, 10)]
    )
    if safe_name in forbidden_names:
        safe_name += "_"

    forbidden_last_chars = [" ", "."]
    if safe_name[-1] in forbidden_last_chars:
        safe_name = safe_name[:-1] + "_"

    # Linux and MacOS restrictions
    forbidden_chars = ["/", "\x00"]
    for char in forbidden_chars:
        safe_name = safe_name.replace(char, "_")

    forbidden_names = [".", ".."]
    if safe_name in forbidden_names:
        safe_name += "_"

    # Limit filename length: https://serverfault.com/a/9548
    safe_name = safe_name[:max_name_length]

    return safe_name if isinstance(path, str) else path.with_name(safe_name)


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


OBSIDIAN_TAG_REGEX = re.compile(r"[^\w/_-]", re.UNICODE)


def normalize_obsidian_tag(tag: str) -> str:
    """
    tag format: https://help.obsidian.md/Editing+and+formatting/Tags#Tag+format

    >>> normalize_obsidian_tag("nested/tag")
    'nested/tag'
    >>> normalize_obsidian_tag("kebab-case")
    'kebab-case'
    >>> normalize_obsidian_tag("snake_case")
    'snake_case'
    >>> normalize_obsidian_tag("grüße-cześć-привет-你好")
    'grüße-cześć-привет-你好'
    >>> normalize_obsidian_tag("mul & tip...le")
    'mul___tip___le'
    >>> normalize_obsidian_tag("1984")
    '1984_'
    >>> normalize_obsidian_tag("y1984")
    'y1984'
    """
    valid_char_tag = OBSIDIAN_TAG_REGEX.sub("_", tag)
    if valid_char_tag.isdigit():
        valid_char_tag += "_"
    return valid_char_tag


class FilesystemImporter:
    """Import notebooks, notes and related data to the filesystem."""

    def __init__(self, progress_bars, config):
        self.frontmatter = config.frontmatter
        self.root_path = None
        self.global_resource_folder = (
            None
            if config.global_resource_folder is None
            else safe_path(config.global_resource_folder)
        )
        self.local_resource_folder = (
            config.local_resource_folder
            if config.local_resource_folder == Path(".")
            else safe_path(config.local_resource_folder)
        )
        # reference id - path (new id)
        self.note_id_map: dict[str, Path] = {}
        self.progress_bars = progress_bars

    def import_resources(self, note: imf.Note):
        assert note.path is not None
        assert self.root_path is not None
        for resource in note.resources:
            self.progress_bars["resources"].update(1)
            resource_title = resource.title or resource.filename.name

            # determine new resource path
            if self.global_resource_folder is None:
                # local resources (next to the markdown files)
                resource_folder = note.path.parent / self.local_resource_folder
                # TODO: done for each resource in each note
                if self.local_resource_folder != Path("."):
                    resource_folder.mkdir(
                        exist_ok=True, parents=len(self.local_resource_folder.parts) > 1
                    )
                resource.path = resource_folder / safe_path(resource.filename.name)
            else:
                # global resource folder
                resource.path = (
                    self.root_path
                    / self.global_resource_folder
                    / safe_path(resource.filename.name)
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

            # Don't create multiple resources for the same file.
            # Cache the original file paths and their corresponding ID.
            if not resource.path.is_file() and resource.filename.is_file():
                shutil.copy(resource.filename, resource.path)
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

    def write_note(self, note: imf.Note):
        assert note.path is not None
        match self.frontmatter:
            case "all":
                metadata = {}
                for field in dataclasses.fields(imf.Note):
                    match field.name:
                        case (
                            "body"
                            | "resources"
                            | "note_links"
                            | "original_id"
                            | "path"
                        ):
                            continue  # included elsewhere or no metadata
                        case "tags":
                            metadata["tags"] = [tag.title for tag in note.tags]
                        case _:
                            if (value := getattr(note, field.name)) is not None:
                                metadata[field.name] = value
                post = frontmatter.Post(note.body, **metadata)
                frontmatter.dump(post, note.path)
            case "joplin":
                # https://joplinapp.org/help/dev/spec/interop_with_frontmatter/
                # Arbitrary metadata will be ignored.
                metadata = {}
                if note.tags:
                    # Convert the tags to lower case before the import to avoid issues
                    # with special first characters.
                    # See: https://github.com/laurent22/joplin/issues/11179
                    metadata["tags"] = [tag.title.lower() for tag in note.tags]
                supported_keys = [
                    "title",
                    "created",
                    "updated",
                    "author",
                    "latitude",
                    "longitude",
                    "altitude",
                ]
                for key in supported_keys:
                    if (value := getattr(note, key)) is not None:
                        metadata[key] = value
                post = frontmatter.Post(note.body, **metadata)
                frontmatter.dump(post, note.path)
            case "obsidian":
                # frontmatter format:
                # https://help.obsidian.md/Editing+and+formatting/Properties#Property+format
                metadata = {}
                if note.tags:
                    metadata["tags"] = [
                        normalize_obsidian_tag(tag.title) for tag in note.tags
                    ]
                    post = frontmatter.Post(note.body, **metadata)
                    frontmatter.dump(post, note.path)
                else:
                    note.path.write_text(note.body, encoding="utf-8")
            case _:
                note.path.write_text(note.body, encoding="utf-8")

    def import_note(self, note: imf.Note):
        assert note.path is not None
        self.progress_bars["notes"].update(1)

        # Handle resources first, since the note body changes.
        self.import_resources(note)

        # needed to properly link notes later
        self.note_id_map[note.reference_id] = note.path

        if len(note.tags) > 0:
            self.progress_bars["tags"].update(len(note.tags))
            if not self.frontmatter:
                LOGGER.warning(
                    f'Tags of note "{note.title}" will be lost without frontmatter.'
                )
        self.write_note(note)

    def import_notebook(self, notebook: imf.Notebook):
        assert notebook.path is not None
        self.progress_bars["notebooks"].update(1)
        if self.root_path is None:
            self.root_path = notebook.path
            if self.global_resource_folder is not None:
                (self.root_path / self.global_resource_folder).mkdir(
                    exist_ok=True, parents=True
                )
        notebook.path.mkdir(exist_ok=True, parents=True)  # TODO
        for note in notebook.child_notes:
            note.path = notebook.path / safe_path(note.title)
            # Don't overwrite existing suffices.
            if note.path.suffix != ".md":
                note.path = note.path.with_suffix(note.path.suffix + ".md")
            try:
                self.import_note(note)
            except Exception as exc:  # pylint: disable=broad-except
                LOGGER.error(f'Failed to write note "{note.title}"')
                LOGGER.debug(exc, exc_info=True)
        for child_notebook in notebook.child_notebooks:
            child_notebook.path = notebook.path / safe_path(child_notebook.title)
            self.import_notebook(child_notebook)

    def update_note_links(self, note: imf.Note):
        assert note.path is not None
        if not note.note_links or not note.body:
            return  # nothing to link
        for note_link in note.note_links:
            self.progress_bars["note_links"].update(1)
            new_path = self.note_id_map.get(note_link.original_id)
            if new_path is None:
                LOGGER.debug(
                    f'Note "{note.title}": '
                    f'could not find linked note: "{note_link.original_text}"'
                )
                continue

            relative_path = get_quoted_relative_path(note.path.parent, new_path)
            note.body = note.body.replace(
                note_link.original_text, f"[{note_link.title}]({relative_path})"
            )
        self.write_note(note)  # update note

    def link_notes(self, notebook: imf.Notebook):
        for note in notebook.child_notes:
            self.update_note_links(note)
        for child_notebook in notebook.child_notebooks:
            self.link_notes(child_notebook)
