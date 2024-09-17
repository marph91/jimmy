This page describes how to import notes from QOwnNotes to markdown.

## General Information

- [Website](https://www.qownnotes.org/)
- Typical extension: Folder with `.md` files (notes), a `media` subfolder (containing resources) and a `notes.sqlite` file (containing tags)

## Instructions

1. [Install jimmy](../index.md#installation)
2. Convert to markdown. Example: `jimmy-cli-linux qownnotes_folder/ --format qownnotes`

## Import Structure

- Markdown style links (`[Link to Markdown Cheatsheet](Markdown Cheatsheet.md)`) and QOwnNotes style links (`<Markdown Cheatsheet.md>`) as described [here](https://www.qownnotes.org/getting-started/markdown.html#links) are converted.

## Known Limitations

- Encrypted notes aren't converted.
