This page describes how to import notes from Day One to Joplin.

## General Information

- [Website](https://dayoneapp.com/)
- Typical extension: `.zip`

## Instructions

1. Export as described in <https://dayoneapp.com/guides/tips-and-tutorials/exporting-entries/>
    1. Choose "Day One JSON (.zip)"
2. [Install jimmy](../index.md#Installation)
3. Import to Joplin. Example: `jimmy-cli-linux Export-Tagebuch.zip --format day_one`

## Import Structure

- Each day is converted to a notebook.
- Entries are converted to notes and grouped into the corresponding notebook of that day.
- Referenced photos are imported as attachments.

## Known Limitations

- Unreferenced photos are not imported.
- Photos that are references by multiple notes are only imported once (i. e. in one note). This seems to be a bug in the Day One export.
- Audio, PDF and video attachments are not imported. They are a Day One premium feature. If you would like to see support, please provide an example file.
