This page describes how to convert notes from single files or folders (recursively) to Markdown.

## Supported Formats

The default conversion covers the following formats:

- Every format that is supported by [Pandoc](https://pandoc.org/). Some formats may need some tweaking, though. A few examples:
    - [Comma-separated values (CSV)](https://en.wikipedia.org/wiki/Comma-separated_values)
    - [DocBook](https://docbook.org/)
    - [DOCX](https://en.wikipedia.org/wiki/Office_Open_XML)
    - [electronic publication (EPUB)](https://www.w3.org/community/epub3/)
    - [HyperText Markup Language (HTML)](https://www.w3.org/html/)
    - [Jupyter Notebook](https://jupyter.org/)
    - [MediaWiki](https://www.mediawiki.org/wiki/Help:Formatting)
    - [OpenDocument-Text (ODT)](https://en.wikipedia.org/wiki/OpenDocument)
    - [Outline Processor Markup Language (OPML)](http://opml.org/)
    - [reStructuredText (RST)](https://docutils.sourceforge.io/rst.html)
    - [Rich Text Format (RTF)](https://en.wikipedia.org/wiki/Rich_Text_Format)
    - [txt2tags](https://txt2tags.org/)
- [AsciiDoc](https://docs.asciidoctor.org/asciidoc/latest/) (requires [Asciidoctor](https://asciidoctor.org/) installed and in path)
- [Email (EML)](https://en.wikipedia.org/wiki/Email#Filename_extensions)
- [Fountain](https://fountain.io/):
    - There is a [built-in Joplin plugin](https://joplinapp.org/help/apps/markdown/#markdown-plugins) that can be activated in the settings.
    - There is a [Obsidian plugin](https://github.com/Darakah/obsidian-fountain).
- Markdown ([CommonMark](https://commonmark.org/))
- TXT

## Instructions

1. [Install Jimmy](../index.md#installation)
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
