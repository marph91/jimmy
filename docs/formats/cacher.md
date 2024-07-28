This page describes how to import notes from Cacher to Joplin.

## General Information

- [Website](https://www.cacher.io/)
- Typical extension: `.json`

## Instructions

1. Export as described in <https://www.cacher.io/docs/guides/snippets/exporting-snippets#how-to-export-1>
2. [Install jimmy](../index.md#installation)
3. Import to Joplin. Example: `jimmy-cli-linux cacher-export-202406182304.json --format cacher`

## Import Structure

- Cacher labels are converted to Joplin tags.
- Cacher snippets are converted to Joplin notebooks.
- Cacher files are converted to Joplin notes.

## Known Limitations

- Only markdown files are converted for now.
- Files attached to snippets are not exported.
