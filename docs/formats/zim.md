# Convert from Zim Wiki to Markdown

## General Information

- [Website](https://zim-wiki.org/)
- Typical extension: Folder with `.txt` files

## Instructions

1. [Install Jimmy](../index.md#installation)
2. Convert to Markdown. Example: `jimmy-cli-linux zim/folder --format zim`
3. [Import to your app](../import_instructions.md)

## Import Structure

Zim does a good job in [exporting to Markdown](https://zim-wiki.org/manual/Help/Export.html). If the built-in export is fine for you, you don't need to use Jimmy.

Jimmy doesn't use Pandoc for conversion and applies some additional tweaks:

- Consistently use ATX style headings (starting with `#`).
- Consistently use spaces instead of tabs.
- Page title and creation date are removed from the note body. They are instead stored in the metadata respectively the filename. The metadata can be included by a front matter.
- Convert Zim checklists to Markdown checklists (`- [ ]`) instead of Markdown lists with signs (`- ☐`). The checklist states are converted as described below:
    - Done and not done are converted to `- [x]`.
    - All other states are converted to `-[ ]`.
