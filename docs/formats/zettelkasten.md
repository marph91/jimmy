This page describes how to convert notes from Zettelkasten (zkn3) to Markdown.

## General Information

- [Website](http://zettelkasten.danielluedecke.de/)
- Typical extension: `.zkn3`

## Instructions

1. [Install jimmy](../index.md#installation)
2. Convert to Markdown. Example: `jimmy-cli-linux test_zettelkasten.zkn3 --format zettelkasten`
3. [Import to your app](../import_instructions.md)

## Import Structure

Zettelkasten supports Markdown export. However, it doesn't convert everything and the note links and attachments get lost. Most data can be preserved, when using the original `.zkn3` location in the filesystem without any export.

- Each zettel is converted to a separate note.
- The note body of Zettelkasten is converted from [BBCode](https://en.wikipedia.org/wiki/BBCode) to Markdown.
- Resources and attachments are converted, if the original folders are next to the `.zkn3` file. I. e. `img` for images and `attachments` for attachments.
- Note sequences (Folgezettel) are linked at the end of the note.

## Known Limitations

Some formatting is not converted, because it can't be expressed in pure Markdown (e. g. alignment).
