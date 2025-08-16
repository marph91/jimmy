---
source_app: QOwnNotes
---

# Convert from QOwnNotes to Markdown

## General Information

- [Website](https://www.qownnotes.org/)
- Typical extension: Folder with `.md` files (notes), a `media` subfolder (containing resources) and a `notes.sqlite` file (containing tags)

## Instructions

1. [Install Jimmy](../index.md#installation)
2. Convert to Markdown. Example: `jimmy-linux cli qownnotes_folder/ --format qownnotes`
3. [Import to your app](../import_instructions.md)

## Import Structure

- Markdown style links (`[Link to Markdown Cheatsheet](Markdown Cheatsheet.md)`) and QOwnNotes style links (`<Markdown Cheatsheet.md>`) as described [here](https://www.qownnotes.org/getting-started/markdown.html#links) are converted.

## Known Limitations

- Encrypted notes aren't converted.
