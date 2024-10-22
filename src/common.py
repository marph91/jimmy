"""Common functions."""

from collections import defaultdict
from dataclasses import dataclass
import datetime as dt
import importlib
import logging
from pathlib import Path
import pkgutil
import random
import tarfile
import tempfile
import time
import uuid
import zipfile

import enlighten
import puremagic

import formats


LOGGER = logging.getLogger("jimmy")


###########################################################
# general
###########################################################


def get_available_formats() -> dict:
    formats_dict = {}
    for module in pkgutil.iter_modules(formats.__path__):
        module_ = importlib.import_module(f"formats.{module.name}")
        accepted_extensions = module_.Converter.accepted_extensions
        accept_folder = module_.Converter.accept_folder
        formats_dict[module.name] = {
            "accepted_extensions": accepted_extensions,
            "accept_folder": accept_folder,
        }
    return formats_dict


def guess_suffix(file_: Path) -> str:
    """
    >>> guess_suffix(Path(__file__))
    '.py'
    >>> guess_suffix(Path("."))
    ''
    >>> guess_suffix(Path("non/existing.txt"))
    ''
    """
    try:
        guessed_suffix = puremagic.from_file(file_)
        # regular jpg files seem to be guessed as jfif sometimes
        if guessed_suffix == ".jfif":
            guessed_suffix = ".jpg"
        return guessed_suffix
    except (FileNotFoundError, IsADirectoryError, puremagic.main.PureError, ValueError):
        return ""


def is_image(file_: Path) -> bool:
    """
    >>> is_image(Path(__file__))
    False
    >>> is_image(Path("."))
    False
    >>> is_image(Path("non/existing.txt"))
    False
    """
    try:
        return puremagic.from_file(file_, mime=True).startswith("image/")
    except (FileNotFoundError, IsADirectoryError, puremagic.main.PureError, ValueError):
        return False


def try_transfer_dicts(source: dict, target: dict, keys: list[str | tuple[str, str]]):
    """Try to transfer values from one to another dict if they exist."""
    for key in keys:
        if isinstance(key, tuple):
            source_key, target_key = key
        else:
            source_key = target_key = key
        if (value := source.get(source_key)) is not None:
            target[target_key] = value


def unique_title() -> str:
    """Create a pseudorandom unique title."""
    return f"unnamed_{uuid.UUID(int=random.getrandbits(128), version=4).hex}"


###########################################################
# stats
###########################################################


class CounterMock:  # pylint: disable=too-few-public-methods
    def update(self, *_):
        pass


@dataclass
class Stats:
    notebooks: int = 0
    notes: int = 0
    resources: int = 0
    tags: int = 0
    note_links: int = 0

    def create_progress_bars(self, no_progress_bars: bool) -> dict:
        if no_progress_bars:
            return defaultdict(CounterMock)
        manager = enlighten.get_manager()
        common = {
            "bar_format": "{desc:11s}{percentage:3.0f}%|{bar}| "
            "{count:{len_total}d}/{total:d} [{elapsed}<{eta}]"
        }
        progress_bars = {}
        if self.notebooks > 0:
            progress_bars["notebooks"] = manager.counter(
                total=self.notebooks, desc="Notebooks", **common
            )
        if self.notes > 0:
            progress_bars["notes"] = manager.counter(
                total=self.notes, desc="Notes", **common
            )
        if self.resources > 0:
            progress_bars["resources"] = manager.counter(
                total=self.resources, desc="Resources", **common
            )
        if self.tags > 0:
            progress_bars["tags"] = manager.counter(
                total=self.tags, desc="Tags", **common
            )
        if self.note_links > 0:
            progress_bars["note_links"] = manager.counter(
                total=self.note_links, desc="Note Links", **common
            )
        # Display all counters:
        # https://python-enlighten.readthedocs.io/en/stable/faq.html#why-isn-t-my-progress-bar-displayed-until-update-is-called
        for progress_bar in progress_bars.values():
            progress_bar.refresh()
        return progress_bars

    def __str__(self):
        if self == Stats():
            return "nothing"
        stats = []
        if self.notebooks > 0:
            stats.append(f"{self.notebooks} notebooks")
        if self.notes > 0:
            stats.append(f"{self.notes} notes")
        if self.resources > 0:
            stats.append(f"{self.resources} resources")
        if self.tags > 0:
            stats.append(f"{self.tags} tags")
        if self.note_links > 0:
            stats.append(f"{self.note_links} note links")
        return ", ".join(stats)


def get_import_stats(parents: list, stats: Stats | None = None) -> Stats:
    if stats is None:
        stats = Stats(len(parents))

    # iterate through all separate inputs
    for parent in parents:
        # iterate through all notebooks
        for notebook in parent.child_notebooks:
            get_import_stats([notebook], stats)

        # assemble stats
        stats.notebooks += len(parent.child_notebooks)
        stats.notes += len(parent.child_notes)
        for note in parent.child_notes:
            stats.resources += len(note.resources)
            stats.tags += len(note.tags)
            stats.note_links += len(note.note_links)

    return stats


###########################################################
# folder operations
###########################################################


def get_single_child_folder(parent_folder: Path) -> Path:
    """If there is only a single subfolder, return it."""
    child_folders = [f for f in parent_folder.iterdir() if f.is_dir()]
    assert len(child_folders) == 1
    return child_folders[0]


def get_temp_folder() -> Path:
    """Return a temporary folder."""
    temp_folder = Path(tempfile.gettempdir()) / f"jimmy_{int(time.time() * 1000)}"
    temp_folder.mkdir(exist_ok=True)
    return temp_folder


def extract_tar(input_: Path) -> Path:
    """Extract a tar file to a new temporary directory."""
    temp_folder = get_temp_folder()
    with tarfile.open(input_) as tar_ref:
        tar_ref.extractall(temp_folder, filter="data")
    return temp_folder


def extract_zip(
    input_: Path, file_to_extract: str | None = None, temp_folder: Path | None = None
) -> Path:
    """Extract a zip file to a new temporary directory."""
    if temp_folder is None:
        temp_folder = get_temp_folder()
    with zipfile.ZipFile(input_) as zip_ref:
        if file_to_extract is None:
            zip_ref.extractall(temp_folder)
        else:
            zip_ref.extract(file_to_extract, temp_folder)
    return temp_folder


def find_file_recursively(root_folder: Path, url: str) -> Path | None:
    potential_matches = sorted(root_folder.rglob(url))
    if not potential_matches:
        LOGGER.debug(f"Couldn't find match for resource {url}")
        return None
    if len(potential_matches) > 1:
        LOGGER.debug(f"Found too many matches for resource {url}")
    return potential_matches[0]


###########################################################
# datetime helpers
###########################################################


def get_ctime_mtime_ms(item: Path) -> dict:
    data = {}
    if (ctime_ms := int(item.stat().st_ctime * 1000)) > 0:
        data["created"] = ctime_ms
    if (mtime_ms := int(item.stat().st_mtime * 1000)) > 0:
        data["updated"] = mtime_ms
    return data


def datetime_to_ms(datetime_: dt.datetime) -> int:
    return int(datetime_.timestamp() * 1000)


def current_unix_ms() -> int:
    return datetime_to_ms(dt.datetime.now())


def date_to_unix_ms(date_: dt.date) -> int:
    # https://stackoverflow.com/a/61886944/7410886
    return datetime_to_ms(
        dt.datetime(year=date_.year, month=date_.month, day=date_.day)
    )


def timestamp_to_datetime(timestamp_s: int | float) -> dt.datetime:
    return dt.datetime.fromtimestamp(timestamp_s, dt.UTC)
