---
source_app: Cacher
---

# Convert from Cacher to Markdown

## General Information

- [Website](https://www.cacher.io/)
- Typical extension: `.json`

## Instructions

1. Export as described [at the website](https://www.cacher.io/docs/guides/snippets/exporting-snippets#how-to-export-1)
2. [Install Jimmy](../index.md#installation)
3. Convert to Markdown. Example: `jimmy-linux cli cacher-export-202406182304.json --format cacher`
4. [Import to your app](../import_instructions.md)

## Compatibility

| Feature | Supported? | Remark |
| --- | :---: | --- |
| Attachments / Images / Resources | ⬜ | |
| Labels / Tags | ✅ | |
| Note Links | ⬜ | |
| Notebook / Folder Hierarchy | ✅ | |
| Rich Text | ✅ | |

## Known Limitations

- Only Markdown files are converted for now.
- Files attached to snippets are not exported.
