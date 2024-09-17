This page describes how to import notes from Synology Note Station to markdown.

## General Information

- [Website](https://www.synology.com/en-global/dsm/feature/note_station)
- Typical extension: `.nsx`

## Instructions

1. Export as described in <https://kb.synology.com/en-global/DSM/help/NoteStation/note_station_managing_notes?version=7#t7>
2. [Install jimmy](../index.md#installation)
3. Convert to markdown. Example: `jimmy-cli-linux notestation-test-books.nsx --format synology_note_station`

## Known Limitations

If you have any of the following issuea and can provide an example file in `.nsx` format, please [open an issue](https://github.com/marph91/jimmy/issues/new/choose) or send me an email.

- Some tables aren't converted. See [here](https://github.com/marph91/jimmy/issues/6#issuecomment-2184924515).
- Some resources aren't converted. See [here](https://github.com/marph91/jimmy/issues/6#issuecomment-2184049255).
- The filetype of resources won't be correct until <https://github.com/laurent22/joplin/issues/10653> is added. Then still non-binary resources (text files like markdown, svg, ...) will be detected incorrectly. The mime type can't be set correctly by API either (see [Joplin thread](https://discourse.joplinapp.org/t/how-does-joplin-determine-the-mime-type-of-a-resource/38726/5)).
- Inline charts are not converted.
