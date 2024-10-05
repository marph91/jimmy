This page describes how to convert notes from Synology Note Station to Markdown.

## General Information

- [Website](https://www.synology.com/en-global/dsm/feature/note_station)
- Typical extension: `.nsx`

## Instructions

1. Export as described in <https://kb.synology.com/en-global/DSM/help/NoteStation/note_station_managing_notes?version=7#t7>
2. [Install jimmy](../index.md#installation)
3. Convert to Markdown. Example: `jimmy-cli-linux notestation-test-books.nsx --format synology_note_station`
4. [Import to your app](../import_instructions.md)

## Known Limitations

Inline charts are not converted.
