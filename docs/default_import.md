The default import can be used to import single files or folders.

## Supported Formats

- Every format that is supported by pandoc. Some formats may need some tweaking, though.
- txt
- [asciidoc](https://docs.asciidoctor.org/asciidoc/latest/) (requires [asciidoctor](https://asciidoctor.org/) installed and in path)

Each file is imported as a note (if conversion was successful). Each folder will be a notebook. You can import single files or a folder recursively. For example a folder of markdown and asciidoc files.

## Examples

```bash
# import a single file supported by pandoc
jimmy libre_office_document.odt

# import multiple files
jimmy plaintext.txt markdown.md

# import all files in a folder
jimmy path/to/folder

# Import all files in a folder. Delete all notes before. I. e. start with a clean workspace.
jimmy path/to/folder --clear-notes
```

After importing, the notes should be available in a new Joplin notebook named like `YYYY-MM-DD HH:MM:SS - Import`.
