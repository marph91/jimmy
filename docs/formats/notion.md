---
source_app: Notion
---

# Convert from Notion to Markdown

## General Information

- [Website](https://www.notion.so/)
- Typical extension: `.zip`

## Instructions

1. Export as described [at the website](https://www.notion.so/help/export-your-content#export-your-entire-workspace)
    1. Choose "Markdown and CSV" and check "Create folder for sub-pages" when exporting.
2. [Install Jimmy](../index.md#installation)
3. Convert to Markdown. Example: `jimmy-linux cli 72a2f31c-3a46-4b44-826d-ae046e693551_Export-d609fb9f-43a4-475d-ba88-1db3e9e6bcd2.zip --format notion`
4. [Import to your app](../import_instructions.md)

## Import Structure

Subpages are linked and converted to Markdown files in a subfolder.
