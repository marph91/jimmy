This page describes how to import notes from jrnl to markdown.

## General Information

- [Website](https://jrnl.sh/)
- Typical extension: `.json`

## Instructions

1. Export as described in <https://jrnl.sh/en/stable/formats/#exporting-with-file>
    1. Export as json to preserve metadata.
    2. Example: `jrnl --format json --file myjournal.json`
2. [Install jimmy](../index.md#installation)
3. Convert to markdown. Example: `jimmy-cli-linux myjournal.json --format jrnl`

## Import Structure

Each journal entry is converted to a separate note in a flat notebook.
