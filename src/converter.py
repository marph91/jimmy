"""Provides the base class for all converters."""

import abc
import logging
from pathlib import Path
import subprocess
from xml.etree import ElementTree as ET

import common
import intermediate_format as imf
import markdown_lib.common
import markdown_lib.eml


class BaseConverter(abc.ABC):
    accepted_extensions: list[str] | None = None
    accept_folder = False

    def __init__(self, config, *_args, **_kwargs):
        self._config = config
        self.logger = logging.getLogger("jimmy")
        self.format = "Jimmy" if config.format is None else config.format
        self.root_notebook: imf.Notebook
        self.root_path: Path
        self.output_folder = config.output_folder

    def prepare_input(self, input_: Path) -> Path:
        """Prepare the input for further processing. For example extract an archive."""
        # define some generally useful conversions
        match input_.suffix.lower():
            case ".bear2bk" | ".textpack":
                temp_folder = common.extract_zip(input_)
                return common.get_single_child_folder(temp_folder)
            case ".jex" | ".tgz" | ".tar.gz":
                return common.extract_tar(input_)
            case ".apkg" | ".nsx" | ".zip" | ".zkn3":
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

    def convert_multiple(self, files_or_folders: list[Path]) -> imf.Notebooks:
        """Main conversion function."""
        notebooks = []
        for input_index, file_or_folder in enumerate(files_or_folders):
            index_suffix = "" if len(files_or_folders) == 1 else f" {input_index}"
            output_folder = self.output_folder.with_name(
                self.output_folder.name + index_suffix
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
    def convert_note(self, *args, **kwargs):
        """
        Convert a single note.

        Some implementation remarks:
        - Should be decorated with @common.catch_all_exceptions to avoid the complete
          conversion to crash.
        - Should log the note title to see some progress.
        """
        # TODO: https://stackoverflow.com/q/19335436/7410886

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

    def remove_empty_notebooks(self, root_notebook: imf.Notebook | None = None):
        """Remove empty notebooks before exporting."""
        if root_notebook is None:
            root_notebook = self.root_notebook
        non_empty_child_notebooks = []
        for notebook in root_notebook.child_notebooks:
            # Remove empty notebooks before the is_empty() check
            # to handle nested empty notebooks.
            self.remove_empty_notebooks(notebook)
            if not notebook.is_empty():
                non_empty_child_notebooks.append(notebook)
        root_notebook.child_notebooks = non_empty_child_notebooks


class DefaultConverter(BaseConverter):
    accepted_extensions = ["*"]
    accept_folder = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # we need a resource folder to avoid writing files to the source folder
        self.resource_folder = common.get_temp_folder()

    def handle_markdown_links(
        self, body: str, path
    ) -> tuple[imf.Resources, imf.NoteLinks]:
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

    @common.catch_all_exceptions
    def convert_note(self, file_: Path, parent: imf.Notebook):
        """Default conversion function for files. Uses pandoc directly."""
        self.logger.debug(f'Converting note "{file_.name}"')
        if common.is_image(file_):
            self.logger.debug("Skipping image")
            return

        format_ = file_.suffix.lower()[1:]
        match format_:
            case "adoc" | "asciidoc" | "asciidoctor":
                # asciidoc -> html -> markdown
                # Technically, the first line is the document title and gets
                # stripped from the note body:
                # https://docs.asciidoctor.org/asciidoc/latest/document/title/
                # However, we want everything in the note body. Thus, we need
                # to use HTML (instead of docbook) as intermediate format.
                # fmt: off
                proc = subprocess.run(
                    [
                        "asciidoctor",
                        # Don't generate the "last updated" footer.
                        # https://stackoverflow.com/a/41777672/7410886
                        "--attribute", "nofooter",
                        "--backend", "html",
                        "--out-file", "-",
                        str(file_.resolve()),
                    ],
                    encoding="utf8",
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                # fmt: on
                if proc.stderr:
                    self.logger.debug(proc.stderr.strip())
                elif proc.returncode != 0:
                    self.logger.warning(f"Asciidoctor error code: {proc.returncode}")
                    return
                note_body = markdown_lib.common.markup_to_markdown(
                    proc.stdout, resource_folder=self.resource_folder
                )
            case "eml":
                note_imf = markdown_lib.eml.eml_to_note(file_, self.resource_folder)
                parent.child_notes.append(note_imf)
                return  # don't use the common conversion
            case "fountain":
                # Simply wrap in a code block. This is supported in
                # Joplin and Obsidian via plugins.
                note_body_fountain = file_.read_text(encoding="utf-8")
                note_body = f"```fountain\n{note_body_fountain}\n```\n"
            case "md" | "markdown" | "txt" | "text":
                note_body = file_.read_text(encoding="utf-8")
            case "docx" | "odt":
                # binary format, supported by pandoc
                note_body = markdown_lib.common.markup_to_markdown(
                    file_.read_bytes(),
                    format_=format_,
                    resource_folder=self.resource_folder,
                )
            case "xml":
                root = ET.parse(file_).getroot()
                root_tag = root.tag.rpartition("}")[-1]  # strip namespace
                match root_tag:
                    case (
                        "endnote"
                        | "mediawiki"
                        | "opml"
                    ):  # TODO: endnotexml and opml example
                        note_body = markdown_lib.common.markup_to_markdown(
                            file_.read_text(encoding="utf-8"),
                            format_=root_tag,
                            resource_folder=self.resource_folder,
                        )
                    # TODO: docbook
                    # case "book":
                    #     note_body = markdown_lib.common.markup_to_markdown(
                    #         file_.read_text(encoding="utf-8"),
                    #         format_="docbook",
                    #         resource_folder=self.resource_folder,
                    #     )
                    case _:
                        note_body = file_.read_text(encoding="utf-8")
            case _:  # last resort
                pandoc_format = markdown_lib.common.PANDOC_INPUT_FORMAT_MAP.get(
                    format_, format_
                )
                note_body = markdown_lib.common.markup_to_markdown(
                    file_.read_text(encoding="utf-8"),
                    format_=pandoc_format,
                    resource_folder=self.resource_folder,
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
            if not file_or_folder.suffix.lower():
                # We can't guess the extension, so we can ignore it.
                self.logger.debug(f"ignored {file_or_folder.name}: No extension.")
                return
            self.convert_note(file_or_folder, parent)
        else:
            self.logger.debug(f"entering folder {file_or_folder.name}")
            new_parent = imf.Notebook(file_or_folder.stem)
            folders = []
            for item in sorted(file_or_folder.iterdir()):
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
        self.convert_file_or_folder(file_or_folder, self.root_notebook)
        # Don't export empty notebooks
        self.remove_empty_notebooks()
