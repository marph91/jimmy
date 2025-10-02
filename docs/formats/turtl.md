---
source_app: Turtl
---

# Convert from Turtl to Markdown

## General Information

- [Website](https://turtlapp.com/)
- Typical extension: `.json`

## Instructions

1. Export as shown [at the website](https://turtlapp.com/features/)
2. [Install Jimmy](../index.md#installation)
3. Convert to Markdown. Example: `jimmy-linux cli turtl-backup.json --format turtl`
4. [Import to your app](../import_instructions.md)

## Compatibility

| Feature | Supported? | Remark |
| --- | :---: | --- |
| Attachments / Images / Resources | ✅ | |
| Labels / Tags | ✅ | |
| Note Links | ⬜ | |
| Notebook / Folder Hierarchy | ✅ | |
| Rich Text | ✅ | |

- Spaces are converted to folders.
- Boards are converted to subfolders of the corresponding space.
- Notes are converted to Markdown files in the corresponding board.
- Tags and files are converted.
