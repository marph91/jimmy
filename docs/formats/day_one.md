---
source_app: Day One
---

# Convert from Day One to Markdown

## General Information

- [Website](https://dayoneapp.com/)
- Typical extension: `.zip`

## Instructions

1. Export as described [at the website](https://dayoneapp.com/guides/tips-and-tutorials/exporting-entries/)
    1. Choose "Day One JSON (.zip)"
2. [Install Jimmy](../index.md#installation)
3. Convert to Markdown. Example: `jimmy-linux cli Export-Tagebuch.zip --format day_one`
4. [Import to your app](../import_instructions.md)

## Compatibility

| Feature | Supported? | Remark |
| --- | :---: | --- |
| Attachments / Images / Resources | ✅ | |
| Labels / Tags | ✅ | |
| Note Links | ✅ | |
| Notebook / Folder Hierarchy | ✅ | |
| Rich Text | ✅ | |

## Known Limitations

- Unreferenced photos are not converted.
- Photos that are references by multiple notes are only imported once (i. e. in one note). This seems to be a bug in the Day One export.
