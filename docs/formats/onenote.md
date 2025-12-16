---
source_app: OneNote
---

# Convert from OneNote to Markdown

## General Information

- [Website](https://www.onenote.com/)
- Typical extension: `.zip` or folder of `.zip` files

## Instructions

!!! warning
    Since 2025, Microsoft seems to have removed the export from below. You might use [Joplin](https://joplinapp.org/help/apps/import_export/#importing-from-onenote) to convert from OneNote to Markdown.

1. Export as described [at the website](https://support.microsoft.com/en-us/office/export-and-import-onenote-notebooks-a4b60da5-8f33-464e-b1ba-b95ce540f309)
2. [Install Jimmy](../index.md#installation)
3. Convert to Markdown. Example: `jimmy-linux cli OneDrive_2024-04-03.zip --format onenote`
4. [Import to your app](../import_instructions.md)

## Compatibility

| Feature | Supported? | Remark |
| --- | :---: | --- |
| Attachments / Images / Resources | ✅ | |
| Labels / Tags | ❎ | |
| Note Links | ✅ | |
| Notebook / Folder Hierarchy | ✅ | |
| Rich Text | ✅ | |

- OneNote notebooks and sections are converted to folders.
- OneNote pages are converted to files.

## Acknowledgements

The converter is based on [one2html](https://github.com/msiemens/one2html) and the single file executable [onenote.rs.exe](https://github.com/marph91/onenote.rs.exe). Thanks for developing it!
