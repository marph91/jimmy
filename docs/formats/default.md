This page describes how to convert notes from single files or folders (recursively) to Markdown.

## Supported Formats

The default import covers the following formats:

- Every format that is supported by [pandoc](https://pandoc.org/). Some formats may need some tweaking, though. A few examples:
    - CSV
    - DocBook
    - DOCX
    - EPUB
    - HTML
    - Jupyter Notebook
    - MediaWiki
    - ODT
    - OPML
    - reStructuredText
    - RTF
    - txt2tags
- [asciidoc](https://docs.asciidoctor.org/asciidoc/latest/) (requires [asciidoctor](https://asciidoctor.org/) installed and in path)
- [Fountain](https://fountain.io/):
    - There is a [built-in Joplin plugin](https://joplinapp.org/help/apps/markdown/#markdown-plugins) that can be activated in the settings.
    - There is a [Obsidian plugin](https://github.com/Darakah/obsidian-fountain).
- Markdown ([Commonmark](https://commonmark.org/))
- txt

## Instructions

1. [Install jimmy](../index.md#installation)
2. Convert to Markdown. Examples:

```sh
# import a single file supported by pandoc
jimmy-cli-linux libre_office_document.odt

# import multiple files
jimmy-cli-linux plaintext.txt markdown.md

# import all files in a folder recursively
jimmy-cli-linux path/to/folder
```

3. [Import to your app](../import_instructions.md)

## Import Structure

- Folders stay folders
- Files are converted to Markdown notes
