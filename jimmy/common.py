"""Common functions."""

import base64
from collections.abc import Callable
import datetime as dt
import difflib
import gzip
import hashlib
import importlib
import logging
from pathlib import Path
import pkgutil
import random
import re
import string
import tarfile
import tempfile
import time
from typing import Any, TypeVar, cast
import uuid
import zipfile

import puremagic
import pydantic

import jimmy.formats


LOGGER = logging.getLogger("jimmy")


###########################################################
# general
###########################################################


MARKDOWN_SUFFIXES = (".md", ".mdown", ".markdown")
F = TypeVar("F", bound=Callable[..., Any])


def catch_all_exceptions(func: F) -> F:
    """
    Decorator to catch all exceptions.
    Useful if many individual notes are converted.
    """

    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.warning(
                'Failed to convert note. Enable the extended log by "--stdout-log-level DEBUG".'
            )
            # https://stackoverflow.com/a/52466005/7410886
            LOGGER.debug(exc, exc_info=True)

    return cast(F, wrapper)


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
        return unique_title()

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

    # Linux and macOS restrictions
    forbidden_chars = ["/", "\x00"]
    for char in forbidden_chars:
        safe_name = safe_name.replace(char, "_")

    forbidden_names = [".", ".."]
    if safe_name in forbidden_names:
        safe_name += "_"

    # Limit filename length: https://serverfault.com/a/9548
    safe_name = safe_name[:max_name_length]

    return safe_name if isinstance(path, str) else path.with_name(safe_name)


def get_unique_path(path: Path, new_content: str | bytes | Path | None = None) -> Path:
    """Get a unique path for a file."""
    if (  # pylint: disable=too-many-boolean-expressions
        # filename is "free"
        not path.exists()
        # byte content is identical
        or isinstance(new_content, bytes)
        and new_content == path.read_bytes()
        or isinstance(new_content, Path)
        and new_content.read_bytes() == path.read_bytes()
        # text content is identical
        or isinstance(new_content, str)
        and new_content == path.read_text()
    ):
        return path

    # Find a new unique name for a duplicated file.
    found_new_name = False
    similar_notes = list(path.parent.glob(f"{path.stem}*{path.suffix}"))
    for new_index in range(1, 10000):
        new_path = path.parent / f"{path.stem}_{new_index:04}{path.suffix}"
        if new_path not in similar_notes:
            found_new_name = True
            break
    if not found_new_name:
        # last resort
        new_path = path.parent / f"{path.stem}_{uuid_title()}{path.suffix}"

    LOGGER.debug(
        f'File "{path.name}" exists already with different content. New name: "{new_path.name}".'
    )
    return new_path


def try_other_suffixes(original_path: Path) -> Path | None:
    """Try to find a file with same name, but different suffix."""
    if not original_path.parent.is_dir():
        LOGGER.debug(f"Folder does not exist: {original_path.parent}")
        return None
    candidates = [item for item in sorted(original_path.parent.iterdir()) if item.is_file()]
    # case sensitive
    for candidate in candidates:
        if original_path.stem == candidate.stem:
            return candidate
    # case insensitive
    for candidate in candidates:
        if original_path.stem.lower() == candidate.stem.lower():
            return candidate
    return None


def write_base64(path: Path, base64_str: str) -> Path:
    """Write a base64 encoded string to a file."""
    content = base64.b64decode(base64_str)
    path = get_unique_path(path, content)
    path.write_bytes(content)
    return path


def get_available_formats() -> dict:
    formats_dict = {}
    for module in pkgutil.iter_modules(jimmy.formats.__path__):
        module_ = importlib.import_module(f"jimmy.formats.{module.name}")
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
    if file_.suffix == ".svm":
        # TODO: Convert ".svm" (StarView Metafile) to a more common format?
        return True
    try:
        return puremagic.from_file(file_, mime=True).startswith("image/")
    except (FileNotFoundError, IsADirectoryError, puremagic.main.PureError, ValueError):
        return False


PASCAL_CASE_RE = re.compile("^(?:[A-Z][a-z]+)+$")


def is_pascal_case(value: str) -> bool:
    """
    https://stackoverflow.com/a/10182901/7410886

    >>> is_pascal_case("camel")
    False
    >>> is_pascal_case("camelCase")
    False
    >>> is_pascal_case("CamelCase")
    True
    >>> is_pascal_case("CAMelCAse")
    False
    >>> is_pascal_case("CAMELCASE")
    False
    >>> is_pascal_case("camelcase")
    False
    >>> is_pascal_case("Camelcase")
    True
    >>> is_pascal_case("Case")
    True
    >>> is_pascal_case("camel_case")
    False
    >>> is_pascal_case("snake-case")
    False
    >>> is_pascal_case("Some words")
    False
    >>> is_pascal_case("~HelloThere")
    False

    # TODO: non-ascii
    # >>> is_pascal_case("Привет")
    # True
    # >>> is_pascal_case("ПриветЛол")
    # True
    # >>> is_pascal_case("Привет, я Лол.")
    # False
    """
    return bool(PASCAL_CASE_RE.match(value))


def to_pascal_case(value: str) -> str:
    """
    https://stackoverflow.com/a/8347192/7410886

    >>> to_pascal_case("abc")
    'Abc'
    >>> to_pascal_case("make IT pascal CaSe")
    'MakeItPascalCase'
    >>> to_pascal_case("PascalCase")
    'PascalCase'
    >>> to_pascal_case("camelCase")
    'Camelcase'
    >>> to_pascal_case("snake_case")
    'SnakeCase'
    >>> to_pascal_case("kebab-case")
    'KebabCase'
    >>> to_pascal_case("PascalCase).")
    'PascalCase'
    >>> to_pascal_case("PascalCase,")
    'PascalCase'
    """
    # TODO: How to handle punctuation?
    value = value.strip(string.punctuation)
    if is_pascal_case(value):
        return value
    for punctuation in string.punctuation:
        value = value.replace(punctuation, " ")
    return value.title().replace(" ", "")


def md5_hash(file_: Path | str) -> str | None:
    try:
        return hashlib.md5(Path(file_).read_bytes()).hexdigest()
    except FileNotFoundError:
        return None


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
    return "unnamed_" + uuid_title()


def uuid_title() -> str:
    return uuid.UUID(int=random.getrandbits(128), version=4).hex


def get_best_match(title: str, note_id_title_map: dict) -> str | None:
    """
    Compare a given string to each string of a sequence and return the best match.
    Useful for linking notes without ID.

    >>> get_best_match('*"quoted", and italic*', {1: "quoted and italic"})
    1
    >>> get_best_match("b", {"a": "a", "b": "b", "c": "c"})
    'b'
    >>> get_best_match("d", {"a": "a", "b": "b", "c": "c"})
    """

    # try to map by title similarity
    match_ratios = [
        difflib.SequenceMatcher(None, title, reference_title).ratio()
        for reference_title in note_id_title_map.values()
    ]
    best_match_ratio = max(match_ratios)
    best_match_id, best_match_title = list(note_id_title_map.items())[
        match_ratios.index(best_match_ratio)
    ]
    if best_match_ratio < 0.6:  # threshold taken from experience
        LOGGER.debug(
            f"Low match ratio: {best_match_ratio:.2f}. Link from "
            f'"{title}" to "{best_match_title}" is not added.'
        )
        return None
    return best_match_id


###########################################################
# stats
###########################################################


class CounterMock:  # pylint: disable=too-few-public-methods
    def update(self, *_):
        pass


@pydantic.dataclasses.dataclass
class Stats:  # pylint: disable=too-few-public-methods
    notebooks: int = 0
    notes: int = 0
    resources: int = 0
    tags: int = 0
    note_links: int = 0

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
    temp_folder = Path(tempfile.gettempdir()) / f"jimmy_{int(time.time() * 10**6)}"
    temp_folder.mkdir(exist_ok=True)
    return temp_folder


def extract_gzip(input_: Path, temp_folder: Path | None = None) -> Path:
    """Extract a gzip file to a new temporary directory."""
    # TODO: Can there be multiple files or folders?
    if temp_folder is None:
        temp_folder = get_temp_folder()
    unzipped_file = temp_folder / input_.stem
    with gzip.open(input_, "rb") as gzip_file:
        unzipped_file.write_bytes(gzip_file.read())
    return unzipped_file


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
    return datetime_to_ms(dt.datetime(year=date_.year, month=date_.month, day=date_.day))


def iso_to_datetime(iso: str) -> dt.datetime:
    """
    >>> iso_to_datetime('2011-11-04T03:00:00')
    datetime.datetime(2011, 11, 4, 3, 0)
    >>> iso_to_datetime('2011-11-04T03:00:00+0200')
    datetime.datetime(2011, 11, 4, 1, 0)
    """
    # parse iso -> (convert to UTC) -> remove timezone

    # Coinvert to UTC if needed.
    # https://docs.python.org/3/library/datetime.html#determining-if-an-object-is-aware-or-naive
    datetime_object = dt.datetime.fromisoformat(iso)
    if datetime_object.tzinfo is None or datetime_object.tzinfo.utcoffset(datetime_object) is None:
        # naive - handle as UTC
        return datetime_object.replace(tzinfo=None)
    # aware - convert to UTC
    return datetime_object.astimezone(dt.UTC).replace(tzinfo=None)


def timestamp_to_datetime(timestamp_s: int | float) -> dt.datetime:
    # parse timestamp -> convert to UTC -> remove timezone
    return dt.datetime.fromtimestamp(timestamp_s, dt.UTC).replace(tzinfo=None)
