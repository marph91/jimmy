This page describes how to convert notes from CherryTree to Markdown.

## General Information

- [Website](https://www.giuspen.net/cherrytree/)
- Typical extension: `.ctd`

## Instructions

1. Export as described in <https://www.giuspen.com/cherrytreemanual/#_exporting>
    1. Choose "Export" -> "Export to CherryTreeDocument" -> "All the Tree" -> "XML, Not Protected (.cdt)"
2. [Install jimmy](../index.md#installation)
3. Convert to Markdown. Example: `jimmy-cli-linux cherry.ctd --format cherrytree`

## Import Structure

- CherryTree nodes are converted to Markdown notes.
- If a CherryTree node contains sub nodes, a folder is created as container. It has the same name as the corresponding note.

## Known Limitations

- Cherrytree checked (`☑`) and crossed checkboxes (`☒`) are converted to Markdown checked checkboxes (`[x]`).
- Cherrytree latex is converted to a Markdown code block.
- Some cherrytree elements are not inserted at their original location, but at the end of the note. This is a limitation of cherrytree's export.
- Cherrytree anchors are not converted.
