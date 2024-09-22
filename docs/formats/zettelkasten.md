This page describes how to convert notes from Zettelkasten to Markdown.

## General Information

- [Website](http://zettelkasten.danielluedecke.de/)
- Typical extension: `.zkn3`

## Instructions

Zettelkasten supports Markdown export. However, it doesn't convert everything and the note links and attachments get lost. Most data can be preserved, when using the original `.zkn3` location in the filesystem without any export.

1. [Install jimmy](../index.md#installation)
2. Convert to Markdown. Example: `jimmy-cli-linux test_zettelkasten.zkn3 --format zettelkasten`
3. [Import to your app](../import_instructions.md)

## Known Limitations

The note body is still formatted in [BBCode](https://en.wikipedia.org/wiki/BBCode) until a good conversion path is available (see [github issue](https://github.com/marph91/jimmy/issues/14)).
