"""Intermediate representation between two note formats."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List


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
    resources: List[Path] = field(default_factory=list)  # list of filenames


@dataclass
class Notebook:
    """Represents a notebook and its children."""

    data: dict
    child_notebooks: List[Notebook] = field(default_factory=list)
    child_notes: List[Note] = field(default_factory=list)
