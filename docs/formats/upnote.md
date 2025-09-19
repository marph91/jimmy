---
source_app: UpNote
---

# Convert from UpNote to Markdown

## General Information

- [Website](https://getupnote.com/)
- Typical extension: Folder containing `.upnx` files

## Instructions

1. Create a manual backup as shown [at the website](https://help.getupnote.com/more/automatic-notes-backup)
    1. Check "Backup attachments"
    2. Select a backup folder. This is the folder you need to pass to Jimmy.
    3. Click "Backup now"
2. [Install Jimmy](../index.md#installation)
3. Convert to Markdown. Example: `jimmy-linux cli UpNote_Backup/ --format upnote`
4. [Import to your app](../import_instructions.md)

!!! note
    The simple HTML export is not suited, since it has a few limitations, like missing note links and no folder hierarchy. The backup contains everything needed.

## Compatibility

| Feature | Supported? | Remark |
| --- | :---: | --- |
| Attachments / Images / Resources | ✅ | |
| Labels / Tags | ✅ | |
| Note Links | ✅ | |
| Notebook / Folder Hierarchy | ✅ | |
| Rich Text | ✅ | |
