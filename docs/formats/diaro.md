---
source_app: Diaro
---

# Convert from Diaro to Markdown

## General Information

- [Website](https://diaroapp.com/)
- Typical extension: `.zip`

## Instructions

1. Create a backup as described [at the website](https://diaroapp.com/faq/how-do-i-backup-my-data-2/)
2. [Install Jimmy](../index.md#installation)
3. Convert to Markdown. Example: `jimmy-linux cli Diaro_20250821.zip --format diaro`
4. [Import to your app](../import_instructions.md)

## Import Structure

- Each Diaro folder is converted to a notebook.
- Entries are converted to notes.
- Tags are preserved.
- Referenced photos are imported as resources.

## Known Limitations

Encrypted backups can't be converted, since the key is not known.
