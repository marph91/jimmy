---
description: Convert from jrnl to Markdown.
---

# Convert from jrnl to Markdown

## General Information

- [Website](https://jrnl.sh/)
- Typical extension: `.json`

## Instructions

1. Export as described [at the website](https://jrnl.sh/en/stable/formats/#exporting-with-file)
    1. Export as JSON to preserve metadata.
    2. Example: `jrnl --format json --file myjournal.json`
2. [Install Jimmy](../index.md#installation)
3. Convert to Markdown. Example: `jimmy-cli-linux myjournal.json --format jrnl`
4. [Import to your app](../import_instructions.md)

## Import Structure

Each journal entry is converted to a separate note in a flat notebook.
