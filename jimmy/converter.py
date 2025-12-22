"""Provides the base class for all converters."""

import abc
import logging
from pathlib import Path
from xml.etree import ElementTree as ET

import frontmatter

from jimmy import common, intermediate_format as imf
import jimmy.variables
import jimmy.md_lib.common
import jimmy.md_lib.convert
import jimmy.md_lib.eml
import jimmy.md_lib.links


class BaseConverter(abc.ABC):
    def __init__(self, config, *_args, **_kwargs):
        self._config = config

        accepted_inputs = jimmy.variables.FORMAT_REGISTRY.get(config.format)
        self.accepted_extensions = accepted_inputs["accepted_extensions"]  # type: ignore[index]
        self.accept_folder = accepted_inputs["accept_folder"]  # type: ignore[index]

        self.logger = logging.getLogger("jimmy")
        self.format = "Jimmy" if config.format is None else config.format
        self.frontmatter = config.frontmatter
        if config.template_file is None:
            self.template = None
        elif not config.template_file.is_file():
            self.logger.warning(
                f'Template file "{config.template_file}" does not exist. Ignoring template.'
            )
            self.template = None
        else:
            self.template = config.template_file.read_text(encoding="utf-8")
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
            input_.suffix.lower() in self.accepted_extensions or self.accepted_extensions == ["*"]
        ):
            return True
        return self.accept_folder and input_.is_dir()

    def convert_multiple(self, files_or_folders: list[Path]) -> imf.Notebooks:
        """Main conversion function."""
        notebooks = []
        for input_index, file_or_folder in enumerate(files_or_folders):
            index_suffix = "" if len(files_or_folders) == 1 else f" {input_index}"
            output_folder = self.output_folder.with_name(self.output_folder.name + index_suffix)
            self.root_notebook = imf.Notebook(output_folder.name, path=output_folder)
            self.root_path = self.prepare_input(file_or_folder)
            # Sanity check - do the input files / folders exist?
            if not file_or_folder.exists():
                self.logger.warning(f"{file_or_folder.resolve()} doesn't exist.")
                continue
            if not self.has_valid_format(file_or_folder):
                self.logger.error("Input file has invalid format.")
                continue
            self.convert(file_or_folder)
            self.apply_postprocessing(self.root_notebook)
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

    def apply_postprocessing(self, root_notebook: imf.Notebook):
        # apply frontmatter/template to all note bodies
        if self.template is not None:
            if self.frontmatter is not None:
                self.logger.warning("Ignoring frontmatter, since a template was specified.")
            for note in root_notebook.child_notes:
                note.apply_template(self.template)
        elif self.frontmatter is not None:
            for note in root_notebook.child_notes:
                note.apply_frontmatter(self.frontmatter)

        for notebook in root_notebook.child_notebooks:
            self.apply_postprocessing(notebook)

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

    def remove_empty_notes(self, root_notebook: imf.Notebook | None = None):
        """Remove empty notes before exporting."""
        if root_notebook is None:
            root_notebook = self.root_notebook
        non_empty_child_notes = []
        for notebook in root_notebook.child_notebooks:
            self.remove_empty_notes(notebook)
        for note in root_notebook.child_notes:
            if not note.is_empty():
                non_empty_child_notes.append(note)
        root_notebook.child_notes = non_empty_child_notes


def decode_strange_ascii(ascii_: str) -> str:
    new_str = []
    for char_ascii in ascii_.split(";"):
        # there are hidden chars, so lstrip() can't be used
        code_ascii = char_ascii.lstrip("\x02amp\x03#")
        if code_ascii:
            new_str.append(chr(int(code_ascii)))
    return "".join(new_str)


class DefaultConverter(BaseConverter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # we need a resource folder to avoid writing files to the source folder
        self.resource_folder = common.get_temp_folder()

    def handle_markdown_links(self, body: str, path: Path) -> tuple[imf.Resources, imf.NoteLinks]:
        note_links = []
        resources = []
        for link in jimmy.md_lib.links.get_markdown_links(body):
            # TODO: fix the source issue not the symptoms
            if "\x02amp\x03" in str(link):
                self.logger.warning(f'Trying to repair corrupted link "{link}".')
                link.text = decode_strange_ascii(link.text)
                link.url = decode_strange_ascii(link.url)
                link.title = decode_strange_ascii(link.title)

            if link.is_web_link or link.is_mail_link:
                continue  # keep the original links
            resource_path = path / link.url
            if resource_path.is_file():
                # TODO: How to distinguish notes from resources properly?
                if resource_path.suffix not in common.MARKDOWN_SUFFIXES:
                    # resource
                    resources.append(imf.Resource(resource_path, str(link), link.text))
                else:
                    # internal link
                    note_links.append(imf.NoteLink(str(link), Path(link.url).stem, link.text))
        return resources, note_links

    @common.catch_all_exceptions
    def convert_note(self, file_: Path, parent: imf.Notebook):
        """Default conversion function for files. Uses pandoc directly."""
        self.logger.debug(f'Converting note "{file_.name}"')
        if common.is_image(file_):
            self.logger.debug("Skipping image")
            return

        note_imf = imf.Note(file_.stem, source_application="jimmy")
        note_imf.time_from_file(file_)

        format_ = file_.suffix.lower()[1:]
        match format_:
            case "adoc" | "asciidoc" | "asciidoctor":
                note_imf.body = jimmy.md_lib.convert.markup_to_markdown(
                    file_.read_text(encoding="utf-8"),
                    pwd=file_.parent,
                    format_="asciidoc",
                    resource_folder=self.resource_folder,
                    # Technically, the first line is the document title and gets
                    # stripped from the note body:
                    # https://docs.asciidoctor.org/asciidoc/latest/document/title/
                    # However, we want everything in the note body. Thus, we need
                    # to create a standalone document and shift the heading level.
                    extra_args=["--shift-heading-level-by=1"],
                )
            case "eml":
                note_imf = jimmy.md_lib.eml.eml_to_note(file_, self.resource_folder)
                parent.child_notes.append(note_imf)
                return  # don't use the common conversion
            case "fountain":
                # Simply wrap in a code block. This is supported in
                # Joplin and Obsidian via plugins.
                note_body_fountain = file_.read_text(encoding="utf-8")
                note_imf.body = f"```fountain\n{note_body_fountain}\n```\n"
            case "md" | "markdown":
                metadata, body = frontmatter.parse(file_.read_text(encoding="utf-8"))
                note_imf.body = body
                # metadata
                for key, value in metadata.items():
                    match key:
                        case (
                            "title"
                            | "author"
                            | "latitude"
                            | "longitude"
                            | "altitude"
                            | "created"
                            | "updated"
                        ):
                            if value is not None:
                                setattr(note_imf, key, value)
                        case "tags":
                            note_imf.tags.extend([imf.Tag(tag) for tag in value])
                        case _:
                            note_imf.custom_metadata[key] = value
            case "txt" | "text":
                note_imf.body = file_.read_text(encoding="utf-8")
            case "docx" | "odt":
                # binary format, supported by pandoc
                note_imf.body = jimmy.md_lib.convert.markup_to_markdown(
                    file_.read_bytes(),
                    pwd=file_.parent,
                    format_=format_,
                    resource_folder=self.resource_folder,
                )
            case "xml":
                root = ET.parse(file_).getroot()
                root_tag = root.tag.rpartition("}")[-1]  # strip namespace
                match root_tag:
                    case "endnote" | "mediawiki" | "opml":  # TODO: endnotexml and opml example
                        note_imf.body = jimmy.md_lib.convert.markup_to_markdown(
                            file_.read_text(encoding="utf-8"),
                            pwd=file_.parent,
                            format_=root_tag,
                            resource_folder=self.resource_folder,
                        )
                    # TODO: docbook
                    # case "book":
                    #     note_imf.body = jimmy.md_lib.convert.markup_to_markdown(
                    #         file_.read_text(encoding="utf-8"),
                    #         pwd=file_.parent,
                    #         format_="docbook",
                    #         resource_folder=self.resource_folder,
                    #     )
                    case _:
                        note_imf.body = file_.read_text(encoding="utf-8")
            case _:  # last resort
                pandoc_format = jimmy.md_lib.convert.PANDOC_INPUT_FORMAT_MAP.get(format_, format_)
                note_imf.body = jimmy.md_lib.convert.markup_to_markdown(
                    file_.read_text(encoding="utf-8"),
                    pwd=file_.parent,
                    format_=pandoc_format,
                    resource_folder=self.resource_folder,
                )

        resources, note_links = self.handle_markdown_links(note_imf.body, file_.parent)
        note_imf.resources = resources
        note_imf.note_links = note_links
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
