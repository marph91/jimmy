---
source_format: Evernote notes
---

# Convert from Evernote to Markdown

## General Information

- [Website](https://evernote.com/)
- Typical extension: `.enex` or folder of `.enex` files

## Instructions

1. Export as described [at the website](https://help.evernote.com/hc/en-us/articles/209005557-Export-notes-and-notebooks-as-ENEX-or-HTML)
    1. Choose "enex"
2. [Install Jimmy](../index.md#installation)
3. Convert to Markdown. Example: `jimmy-linux cli backup.enex --format evernote`
    1. To decrypt encrypted notes, specify your password, like `jimmy-linux cli backup.enex --format evernote --password 1234`
4. [Import to your app](../import_instructions.md)

## Compatibility

| Feature | Supported? | Remark |
| --- | :---: | --- |
| Attachments / Images / Resources | ✅ | |
| Labels / Tags | ✅ | |
| Note Links | ✅ | |
| Notebook / Folder Hierarchy | ✅ | |
| Rich Text | ✅ | |
