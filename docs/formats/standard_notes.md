---
source_app: Standard Notes
---

# Convert from Standard Notes to Markdown

## General Information

- [Website](https://standardnotes.com/)
- Typical extension: `.zip`

## Instructions

1. Export as described [at the website](https://standardnotes.com/help/14/how-do-i-create-and-import-backups-of-my-standard-notes-data)
2. [Install Jimmy](../index.md#installation)
3. Convert to Markdown. Example: `jimmy-cli-linux "Standard Notes Backup - Sun Apr 28 2024 12_56_55 GMT+0200.zip" --format standard_notes`
4. [Import to your app](../import_instructions.md)

## Import Structure

Notes in "Super" format are converted to Markdown. Other notes are taken as-is.

## Known Limitations

Note links, attachments and folders are not implemented yet, since they require a subscription.
