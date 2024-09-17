This page describes how to import notes from [x]it! to markdown.

## General Information

- [Website](https://xit.jotaen.net/)
- Typical extension: `.xit`

## Instructions

1. [Install jimmy](../index.md#installation)
2. Convert to markdown. Example: `jimmy-cli-linux example.xit --format xit`

## Import Structure

- xit groups are converted to folders
- xit items are converted to markdown todos
- Priority, tags and due dates are converted to metadata and removed from the todo title
