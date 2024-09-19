This page describes how to convert notes from Cacher to Markdown.

## General Information

- [Website](https://www.cacher.io/)
- Typical extension: `.json`

## Instructions

1. Export as described in <https://www.cacher.io/docs/guides/snippets/exporting-snippets#how-to-export-1>
2. [Install jimmy](../index.md#installation)
3. Convert to Markdown. Example: `jimmy-cli-linux cacher-export-202406182304.json --format cacher`

## Import Structure

- Cacher labels are converted to tags.
- Cacher snippets are converted to folders.
- Cacher files are converted to Markdown notes.

## Known Limitations

- Only Markdown files are converted for now.
- Files attached to snippets are not exported.
