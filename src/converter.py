"""Provides the base class for all converters."""

import abc
import logging
from pathlib import Path
import subprocess

import pypandoc

import common
import intermediate_format as imf
import markdown_lib.common


class BaseConverter(abc.ABC):
    accepted_extensions: list[str] | None = None
    accept_folder = False

    def __init__(self, format_: str, output_folder):
        self.logger = logging.getLogger("jimmy")
        self.format = "Jimmy" if format_ is None else format_
        self.root_notebook: imf.Notebook
        self.root_path: Path
        self.output_folder = output_folder

    def prepare_input(self, input_: Path) -> Path:
        """Prepare the input for further processing. For example extract an archive."""
        # define some generally useful conversions
        match input_.suffix.lower():
            case ".bear2bk" | ".textpack":
                temp_folder = common.extract_zip(input_)
                return common.get_single_child_folder(temp_folder)
            case ".jex" | ".tgz" | ".tar.gz":
                return common.extract_tar(input_)
            case ".nsx" | ".zip" | ".zkn3":
                return common.extract_zip(input_)
            case _:  # ".textbundle", folder
                return input_

    def has_valid_format(self, input_: Path) -> bool:
        """Check if the input has a valid format."""
        if self.accepted_extensions is not None and (
            input_.suffix.lower() in self.accepted_extensions
            or self.accepted_extensions == ["*"]
        ):
            return True
        return self.accept_folder and input_.is_dir()

    def convert_multiple(self, files_or_folders: list[Path]) -> list[imf.Notebook]:
        """Main conversion function."""
        notebooks = []
        for input_index, file_or_folder in enumerate(files_or_folders):
            index_suffix = "" if len(files_or_folders) == 1 else f" {input_index}"
            output_folder = self.output_folder.with_name(
                self.output_folder.stem + index_suffix
            )
            self.root_notebook = imf.Notebook(output_folder.name, path=output_folder)
            self.root_path = self.prepare_input(file_or_folder)
            # Sanity check - do the input files / folders exist?
            if not file_or_folder.exists():
                self.logger.warning(f"{file_or_folder.resolve()} doesn't exist.")
                continue
            if not self.has_valid_format(file_or_folder):
                self.logger.warning(f"{file_or_folder} has invalid format.")
                continue
            self.convert(file_or_folder)
            notebooks.append(self.root_notebook)
        return notebooks

    @abc.abstractmethod
    def convert(self, file_or_folder: Path):
        """Conversion function for a single input."""
        # example implementation:
        # - extract notebooks and their title
        # - append to the root notebook
        # - for each note in a notebook:
        #     - extract the title
        #     - log the title
        #     - extract the body and metadata
        #     - extract resources
        #     - extract tags
        #     - extract note links
        #     - append note to the notebook


class DefaultConverter(BaseConverter):
    accepted_extensions = ["*"]
    accept_folder = True

    def handle_markdown_links(self, body: str, path) -> tuple[list, list]:
        note_links = []
        resources = []
        for link in markdown_lib.common.get_markdown_links(body):
            if link.is_web_link or link.is_mail_link:
                continue  # keep the original links
            resource_path = path / link.url
            if resource_path.is_file():
                if common.is_image(resource_path):
                    # resource
                    resources.append(imf.Resource(resource_path, str(link), link.text))
                else:
                    # TODO: this could be a resource, too. How to distinguish?
                    # internal link
                    note_links.append(
                        imf.NoteLink(str(link), Path(link.url).stem, link.text)
                    )
        return resources, note_links

    def convert_file(self, file_: Path, parent: imf.Notebook):
        """Default conversion function for files. Uses pandoc directly."""
        match file_.suffix.lower():
            case ".md" | ".markdown" | ".txt" | ".text":
                note_body = file_.read_text(encoding="utf-8")
            case ".fountain":
                # Simply wrap in a code block. This is supported in
                # Joplin and Obsidian via plugins.
                note_body_fountain = file_.read_text(encoding="utf-8")
                note_body = f"```fountain\n{note_body_fountain}\n```\n"
            case ".adoc" | ".asciidoc":
                # asciidoc -> html -> markdown
                # Technically, the first line is the document title and gets
                # stripped from the note body:
                # https://docs.asciidoctor.org/asciidoc/latest/document/title/
                # However, we want everything in the note body. Thus, we need
                # to use HTML (instead of docbook) as intermediate format.
                # fmt: off
                note_body_html = subprocess.check_output(
                    [
                        "asciidoctor",
                        "--backend", "html",
                        "--out-file", "-",
                        str(file_.resolve()),
                    ]
                )
                # fmt: on
                note_body = markdown_lib.common.markup_to_markdown(
                    note_body_html.decode()
                )
                note_body_splitted = note_body.split("\n")
                if note_body_splitted[-2].startswith("Last updated "):
                    # Remove unnecessarily added lines if needed.
                    note_body = "\n".join(note_body_splitted[:-2])
            case _:
                note_body = pypandoc.convert_file(
                    file_,
                    markdown_lib.common.PANDOC_OUTPUT_FORMAT,
                    # somehow the temp folder is needed to create the resources properly
                    extra_args=[f"--extract-media={common.get_temp_folder()}"],
                )

        resources, note_links = self.handle_markdown_links(note_body, file_.parent)
        note_imf = imf.Note(
            file_.stem,
            note_body,
            source_application="jimmy",
            resources=resources,
            note_links=note_links,
        )
        note_imf.time_from_file(file_)
        parent.child_notes.append(note_imf)

    def convert_file_or_folder(self, file_or_folder: Path, parent: imf.Notebook):
        """Default conversion function for folders."""
        if file_or_folder.is_file():
            try:
                self.convert_file(file_or_folder, parent)
                self.logger.debug(f"ok   {file_or_folder.name}")
            except Exception as exc:  # pylint: disable=broad-except
                self.logger.debug(
                    f"fail {file_or_folder.name}: {str(exc).strip()[:120]}"
                )
        else:
            self.logger.debug(f"entering folder {file_or_folder.name}")
            new_parent = imf.Notebook(file_or_folder.stem)
            folders = []
            for item in file_or_folder.iterdir():
                if item.is_file():
                    self.convert_file_or_folder(item, new_parent)
                else:
                    # Delay processing folders to have a better readable log. I. e.
                    # folder 1 - file 1, file 2, file 3
                    # folder 2 - file 1, file 2, file 3
                    # TODO: check if there is a better way
                    folders.append(item)
            for folder in folders:
                self.convert_file_or_folder(folder, new_parent)
            parent.child_notebooks.append(new_parent)

    def convert(self, file_or_folder: Path):
        self.root_path = file_or_folder
        self.convert_file_or_folder(file_or_folder, self.root_notebook)
