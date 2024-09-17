This page describes how to import notes from Day One to markdown.

## General Information

- [Website](https://dayoneapp.com/)
- Typical extension: `.zip`

## Instructions

1. Export as described in <https://dayoneapp.com/guides/tips-and-tutorials/exporting-entries/>
    1. Choose "Day One JSON (.zip)"
2. [Install jimmy](../index.md#installation)
3. Convert to markdown. Example: `jimmy-cli-linux Export-Tagebuch.zip --format day_one`

## Import Structure

- Each day is converted to a notebook.
- Entries are converted to notes and grouped into the corresponding notebook of that day.
- Referenced Audios, PDF, photos and videos are imported as resources.

## Known Limitations

- Unreferenced photos are not imported.
- Photos that are references by multiple notes are only imported once (i. e. in one note). This seems to be a bug in the Day One export.
