"""Intermediate representation between two note formats."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


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

    @property
    def is_image(self) -> bool:
        # Just take the supported image types of Joplin:
        # https://github.com/laurent22/joplin/blob/a3eec19b32684b86202c751c94c092c7339c6307/packages/lib/models/utils/resourceUtils.ts#L40-L43
        return self.filename.suffix.lower() in (
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".svg",
            ".webp",
            ".avif",
        )


@dataclass
class Tag:
    """Represents a tag."""

    data: dict
    original_id: str


@dataclass
class Note:
    """Represents a note."""

    data: dict
    tags: list[Tag] = field(default_factory=list)
    resources: list[Resource] = field(default_factory=list)
    # list of complete links including original note ids
    note_links: list[NoteLink] = field(default_factory=list)
    original_id: str | None = None
    joplin_id: str | None = None


@dataclass
class Notebook:
    """Represents a notebook and its children."""

    data: dict
    child_notebooks: list[Notebook] = field(default_factory=list)
    child_notes: list[Note] = field(default_factory=list)
