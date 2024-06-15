The default import can be used to import single files or folders recursively.

## Export instructions

The default import covers the following formats:

- Every format that is supported by [pandoc](https://pandoc.org/). Some formats may need some tweaking, though. A few examples:
    - CSV
    - DocBook
    - docx
    - EPUB
    - HTML
    - Jupyter notebook
    - ODT
    - OPML
    - MediaWiki
    - reStructuredText
    - RTF
    - txt2tags
- [asciidoc](https://docs.asciidoctor.org/asciidoc/latest/) (requires [asciidoctor](https://asciidoctor.org/) installed and in path)
- Markdown
- txt

## Import to Joplin

Examples:

```sh
# import a single file supported by pandoc
jimmy-cli-linux libre_office_document.odt

# import multiple files
jimmy-cli-linux plaintext.txt markdown.md

# import all files in a folder recursively
jimmy-cli-linux path/to/folder
```

## Import structure

- Folders are converted to Joplin notebooks
- Files are converted to Joplin notes
