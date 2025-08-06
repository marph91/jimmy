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

## Import Structure

- Each `.enex` file is converted to a folder.
- Notes inside the `.enex` file are converted to Markdown files.
- Note links are recovered by matching the note name. This might not work sometimes, if the name was changed after creating the link.
