# Import Instructions

This page describes how you can import the notes that you just converted to Markdown.

## Any Editor

Open the root folder in the editor.

## Joplin

[General import instructions from the Joplin website.](https://joplinapp.org/help/apps/import_export/#importing-from-markdown-files)

1. In Joplin, go to `File -> Import` and choose:
    - `MD - Markdown (Directory)` if you converted without frontmatter. This is the default.
    - `MD - Markdown + Front Matter (Directory)` if you converted with frontmatter. You can add frontmatter by using the `--frontmatter joplin` argument.
2. Select the root folder.

## Logseq

Since Logseq doesn't support folders, this will only work with "flat exports". I. e. where all Markdown files are in the root folder. It works for example with [Google Keep](formats/google_keep.md).

1. Use the arguments `--output-folder "pages" --global-resource-folder "../assets"`. This exports the Markdown notes to the `pages` folder and the resources next to it in a `assets` folder. Just like it is in Logseq. A complete command could look like `jimmy-cli-linux takeout-20240401T160516Z-001.zip --format google_keep --output-folder "pages" --global-resource-folder "../assets"`
2. Either copy the folders to your Logseq graph or open them as new graph to check how it looks.

## Obsidian

[General import instructions from the Obsidian website.](https://help.obsidian.md/import/markdown)

- Copy the root folder to you vault or open it as a new vault.
- You can add metadata in the frontmatter by using the `--frontmatter obsidian` argument.

## QOwnNotes

1. Use the argument `--local-resource-folder media`. This is not required, but aligns with the internal structure of QOwnNotes.
2. Copy the root folder to you note folder or open it as a new note folder.
3. Enable subfolders by `Note -> Settings -> Use note subfolders`.

## Notion

[General import instructions from the Notion website.](https://www.notion.so/help/import-data-into-notion)

This will only import your Markdown notes. Importing resources seems to be not supported.

## VNote

Choose "Import Folder" as described in the [documentation](https://vnote.readthedocs.io/en/latest/docs/en_us/docs/Users/Notes%20Management.html?#import-files-and-folders).
