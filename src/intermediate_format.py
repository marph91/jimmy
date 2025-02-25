"""Intermediate representation between two note formats."""

from __future__ import annotations

import dataclasses
import datetime as dt
import logging
from pathlib import Path
import re

import frontmatter
import pydantic

import common


LOGGER = logging.getLogger("jimmy")
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


@pydantic.dataclasses.dataclass
class NoteLink:
    """Represents an internal link from one note to another note."""

    # This text will be replaced with the path to the linked file after conversion.
    original_text: str
    # For convenience. Should be included in "original_text", too.
    original_id: str
    # [title_or_original_id](:/original_id)
    title: str


@pydantic.dataclasses.dataclass
class Resource:
    """Represents a resource."""

    filename: Path
    # This text will be replaced with the path to the resource after conversion.
    # If None, the resource gets appended.
    original_text: str | None = None
    # [title_or_filename](:/resource_id)
    title: str | None = None

    # internal data
    is_image: bool = dataclasses.field(init=False)
    md5: str | None = None
    path: Path | None = None

    def __post_init__(self):
        # resolve the user directory to prevent issues with puremagic
        self.filename = self.filename.expanduser()
        # We can't simply match by extension, because sometimes the files/images
        # are stored as binary blob without extension.
        self.is_image = common.is_image(self.filename)
        # md5 checksum for detecting duplicated resources
        self.md5 = common.md5_hash(self.filename)

    def __eq__(self, other: object) -> bool:
        """Equality based on the md5 hash."""
        # Don't match by type(): https://stackoverflow.com/a/72295907/7410886
        match other:
            case Path() | str():
                return self.md5 == common.md5_hash(other)
            case Resource():
                return self.md5 == other.md5
        raise NotImplementedError(f"Can't compare {type(self)} with {type(other)}.")

    def __hash__(self):
        return hash(self.original_text)


@pydantic.dataclasses.dataclass
class Tag:
    """Represents a tag."""

    title: str

    # internal data
    original_id: str | None = None

    @property
    def reference_id(self) -> str:
        """
        Reference ID of the original app. Might be not unique,
        but this is sufficient for now.
        """
        return self.original_id or self.title


@pydantic.dataclasses.dataclass
class Note:
    """Represents a note."""

    title: str
    body: str = ""
    created: dt.datetime | None = None
    updated: dt.datetime | None = None
    author: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    altitude: float | None = None

    source_application: str | None = None

    # internal data
    tags: Tags = dataclasses.field(default_factory=list)
    resources: Resources = dataclasses.field(default_factory=list)
    # list of complete links including original note ids
    note_links: NoteLinks = dataclasses.field(default_factory=list)
    original_id: str | None = None
    path: Path | None = None

    @property
    def reference_id(self) -> str:
        """
        Reference ID of the original app. Might be not unique,
        but this is sufficient for now.
        """
        return self.original_id or self.title

    def time_from_file(self, file_: Path):
        self.created = common.timestamp_to_datetime(file_.stat().st_ctime)
        self.updated = common.timestamp_to_datetime(file_.stat().st_mtime)

    def is_empty(self) -> bool:
        return not self.body.strip() and not self.tags and not self.resources

    def apply_template(self, template: str):
        available_variables: dict = {}
        for field in dataclasses.fields(Note):
            if field.name in ("note_links", "resources", "tags"):
                available_variables[field.name] = [
                    tag.title for tag in getattr(self, field.name) if tag.title.strip()
                ]
            else:
                if (value := getattr(self, field.name)) is not None:
                    available_variables[field.name] = value
                else:
                    available_variables[field.name] = "null"  # yaml format
        self.body = template.format(**available_variables)

    def apply_frontmatter(self, frontmatter_: str):
        match frontmatter_:
            case "joplin":
                # https://joplinapp.org/help/dev/spec/interop_with_frontmatter/
                # Arbitrary metadata will be ignored.
                metadata: dict = {}
                for field in dataclasses.fields(Note):
                    match field.name:
                        case "title" | "author" | "latitude" | "longitude" | "altitude":
                            if (value := getattr(self, field.name)) is not None:
                                metadata[field.name] = value
                        case "created" | "updated":
                            if (value := getattr(self, field.name)) is not None:
                                metadata[field.name] = value.isoformat()
                        case "tags":
                            if not self.tags:
                                continue
                            # Convert the tags to lower case before the import to
                            # avoid issues with special first characters.
                            # See: https://github.com/laurent22/joplin/issues/11179
                            metadata["tags"] = [tag.title.lower() for tag in self.tags]
                post = frontmatter.Post(self.body, **metadata)
                self.body = frontmatter.dumps(post)
            case "obsidian":
                # frontmatter format:
                # https://help.obsidian.md/Editing+and+formatting/Properties#Property+format
                metadata = {}
                if self.tags:
                    metadata["tags"] = [
                        normalize_obsidian_tag(tag.title) for tag in self.tags
                    ]
                    post = frontmatter.Post(self.body, **metadata)
                    self.body = frontmatter.dumps(post)
            case "qownnotes":
                # space separated tags, as supported by:
                # - https://github.com/qownnotes/scripts/tree/master/epsilon-notes-tags
                # - https://github.com/qownnotes/scripts/tree/master/yaml-nested-tags
                if self.tags:
                    post = frontmatter.Post(
                        self.body, tags=" ".join([tag.title for tag in self.tags])
                    )
                    self.body = frontmatter.dumps(post)
            case _:
                LOGGER.debug(f'Ignoring unknown frontmatter "{frontmatter_}"')


@pydantic.dataclasses.dataclass
class Notebook:
    """Represents a notebook and its children."""

    title: str
    created: dt.datetime | None = None
    updated: dt.datetime | None = None

    # internal data
    child_notebooks: Notebooks = dataclasses.field(default_factory=list)
    child_notes: Notes = dataclasses.field(default_factory=list)
    original_id: str | None = None
    path: Path | None = None

    def is_empty(self) -> bool:
        return not self.child_notebooks and not self.child_notes


# some type definitions for convenience
Notes = list[Note]
Notebooks = list[Notebook]
NoteLinks = list[NoteLink]
Resources = list[Resource]
Tags = list[Tag]
