---
source_app: Samsung Notes
---

# Convert from Samsung Notes to Markdown

## General Information

- [Website](https://www.samsung.com/uk/apps/samsung-notes/)
- Typical extensions: Folder with `.docx` files

!!! note
    These instructions don't work with `.snb` files from the old S-Note app. You might try [this script](https://github.com/LucasMatuszewski/snb2md-recursive) instead.

## Instructions

1. Select the notes to export and choose "Save as file → Microsoft Word file"
2. [Install Jimmy](../index.md#installation)
3. Convert to Markdown. Example: `jimmy-linux cli export/folder/`
4. [Import to your app](../import_instructions.md)

## Compatibility

| Feature | Supported? | Remark |
| --- | :---: | --- |
| Attachments / Images / Resources | ✅ | |
| Labels / Tags | ❎ | |
| Note Links | ⬜ | |
| Notebook / Folder Hierarchy | ❎ | |
| Rich Text | ✅ | |

## Known Limitations

- Tags and folder hierarchy are not preserved. The information is lost when exporting from Samsung Notes already.
- Attachments are not preserved.
- Most of the markup is not preserved.

## Notes on the proprietary .sdocx format

It would be desirable to convert Samsung Notes `.sdocx` files directly, as they should contain all information. The `.sdocx` files are zip archives with content:

```
├── abc8fd18-01b9-11f0-8139-fb1a97747e58.page
├── abc90452-01b9-11f0-9538-4bbfa19fc222.page
├── end_tag.bin
├── media
│   └── mediaInfo.dat
├── note.note
└── pageIdInfo.dat
```

It was not possible to reverse engineer the binary files in a reasonable amount of time, though. If you have any information about the layout, please share.
