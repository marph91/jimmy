---
source_app: FuseBase and Nimbus Note
---

# Convert from FuseBase to Markdown

## General Information

- [Website](https://nimbusweb.me/note/)
- FuseBase was formerly called Nimbus Note
- Typical extension: `.zip` or folder with `.zip` files

## Instructions

1. Export as described [at the website](https://nimbusweb.me/guides/settings/how-to-export-notes-to-html-or-pdf/)
2. [Install Jimmy](../index.md#installation)
3. Convert to Markdown. Example: `jimmy-linux cli nimbus_note/Example/ --format nimbus_note`
4. [Import to your app](../import_instructions.md)

## Known Limitations

- Tags aren't included in single page exports.

If you have a backup including tags and note links (premium feature), feel free to share.

!!! note
    It was possible to [export multiple pages at once as JSON or HTML](https://discourse.joplinapp.org/t/feature-request-nimbus-notes-import/5165/7). As of 2025, both options appear to have been removed. It is now only possible to export individual pages. Please ask their support for the reason.
