This page describes how to convert notes from Samsung Notes to Markdown.

## General Information

- [Website](https://www.samsung.com/uk/apps/samsung-notes/)
- Typical extensions: Folder with `.docx` files

!!! note These instructions don't work with `.snb` files from the old S-Note app. You might try [this script](https://github.com/LucasMatuszewski/snb2md-recursive) instead.

## Instructions

1. Select the notes to export and choose "Save as file > Microsoft Word file"
2. [Install Jimmy](../index.md#installation)
3. Convert to Markdown. Example: `jimmy-cli-linux export/folder/`
4. [Import to your app](../import_instructions.md)

## Known Limitations

- Tags and folder hierarchy are not preserved. The information is lost when exporting from Samsung Notes already.
- Attachments are not preserved.
- Most of the markup is not preserved.
