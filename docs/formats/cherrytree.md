- [Website](https://www.giuspen.net/cherrytree/)
- Typical extension: `.ctd`

## Export instructions

- <https://www.giuspen.com/cherrytreemanual/#_exporting>
- Choose "Export" -> "Export to CherryTreeDocument" -> "All the Tree" -> "XML, Not Protected (.cdt)"

## Import to Joplin

Example: `jimmy-cli-linux cherry.ctd --format cherrytree`

## Import structure

- CherryTree nodes are converted to Joplin notes.
- If a CherryTree node contains sub nodes, a Joplin Notebook is created as container. It has the same name as the corresponding note.

## Known limitations

- Cherrytree checked (`☑`) and crossed checkboxes (`☒`) are converted to markdown checked checkboxes (`[x]`).
- Cherrytree latex is converted to a markdown code block.
- Some cherrytree elements are not inserted at their original location, but at the end of the note. This is a limitation of cherrytree's export.
- Cherrytree anchors are not converted.
