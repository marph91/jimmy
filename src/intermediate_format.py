"""Intermediate representation between two note formats."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List


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
    original_text: Optional[str] = None
    # [title_or_filename](:/resource_id)
    title: Optional[str] = None


@dataclass
class Tag:
    """Represents a tag."""

    data: dict
    original_id: str


@dataclass
class Note:
    """Represents a note."""

    data: dict
    tags: List[Tag] = field(default_factory=list)
    resources: List[Resource] = field(default_factory=list)
    # list of complete links including original note ids
    note_links: List[NoteLink] = field(default_factory=list)
    original_id: Optional[str] = None
    joplin_id: Optional[str] = None


@dataclass
class Notebook:
    """Represents a notebook and its children."""

    data: dict
    child_notebooks: List[Notebook] = field(default_factory=list)
    child_notes: List[Note] = field(default_factory=list)
