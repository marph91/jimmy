"""Intermediate representation between two note formats."""

from __future__ import annotations

from dataclasses import dataclass, field
import datetime as dt
from pathlib import Path

import common


@dataclass
class NoteLink:
    """Represents an internal link from one note to another note."""

    # This text will be replaced with the Joplin-internal resource ID.
    original_text: str
    # For convenience. Should be included in "original_text", too.
    original_id: str
    # [title](:/resource_id)
    title: str


@dataclass
class Resource:
    """Represents a resource."""

    filename: Path
    # This text will be replaced with the Joplin-internal resource ID.
    # If None, the resource gets appended.
    original_text: str | None = None
    # [title_or_filename](:/resource_id)
    title: str | None = None

    # internal data
    is_image: bool = field(init=False)
    path: Path | None = None

    def __post_init__(self):
        # Supported image types of Joplin:
        # https://github.com/laurent22/joplin/blob/a3eec19b32684b86202c751c94c092c7339c6307/packages/lib/models/utils/resourceUtils.ts#L40-L43
        # We can't simply match by extension, because sometimes the files/images
        # are stored as binary blob without extension.
        self.is_image = common.is_image(self.filename)


@dataclass
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


@dataclass
class Note:
    """Represents a note."""

    # pylint: disable=too-many-instance-attributes
    title: str
    body: str = ""
    created: dt.datetime | None = None
    updated: dt.datetime | None = None
    author: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    altitude: float | None = None

    # TODO: remove?
    source_application: str | None = None

    # internal data
    tags: list[Tag] = field(default_factory=list)
    resources: list[Resource] = field(default_factory=list)
    # list of complete links including original note ids
    note_links: list[NoteLink] = field(default_factory=list)
    original_id: str | None = None
    joplin_id: str | None = None
    path: Path | None = None

    @property
    def reference_id(self) -> str:
        """
        Reference ID of the original app. Might be not unique,
        but this is sufficient for now.
        """
        return self.original_id or self.title

    def time_from_file(self, file_: Path):
        self.created = dt.datetime.utcfromtimestamp(file_.stat().st_ctime)
        self.updated = dt.datetime.utcfromtimestamp(file_.stat().st_mtime)


@dataclass
class Notebook:
    """Represents a notebook and its children."""

    title: str
    created: dt.datetime | None = None
    updated: dt.datetime | None = None

    # internal data
    child_notebooks: list[Notebook] = field(default_factory=list)
    child_notes: list[Note] = field(default_factory=list)
    original_id: str | None = None
    path: Path | None = None
