This page describes how to import notes from Zoho Notebook to Joplin.

## General Information

- [Website](https://www.zoho.com/notebook/)
- Typical extension: `.zip`

## Instructions

1. Export as described in <https://help.zoho.com/portal/en/kb/notebook/import-and-export/articles/export-all-your-notecards-from-notebook>
    1. Export as HTML
2. [Install jimmy](../index.md#installation)
3. Import to Joplin. Example: `jimmy-cli-linux Notebook_14Apr2024_1300_html.zip --format zoho_notebook`

## Known Limitations

- Checklists are converted to plain lists. This might change with a newer pandoc version.
