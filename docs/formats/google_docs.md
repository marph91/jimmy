---
description: Convert from Google Docs to Markdown.
---

# Convert from Google Docs to Markdown

## General Information

- [Website](https://docs.google.com/)
- Typical extensions: `.zip`, `.tgz`

## Instructions

1. Export via [Google Takeout](https://takeout.google.com)
    1. Select "Drive"
    2. Select the folders you want to export
2. [Install Jimmy](../index.md#installation)
3. Convert to Markdown. Example: `jimmy-cli-linux takeout-20240401T160556Z-001.zip --format google_docs`
4. [Import to your app](../import_instructions.md)
