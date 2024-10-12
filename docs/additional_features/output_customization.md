The output can be customized in the following ways.

## Frontmatter

Include Markdown frontmatter by `--frontmatter`. Currently, Joplin and Obsidian compatible frontmatter (`--frontmatter joplin` respectively `--frontmatter obsidian`) can be generated. Alternatively, all available metadata can be included (`--frontmatter all`).

## Output Folder

The output folder can be specified by `--output-folder OUTPUT_FOLDER`.

## Resource Location

Resources are stored by default next to the Markdown file. When using `--local-resource-folder FOLDER`, the resources are stored relative to the Markdown files. For example in an `media` folder, like in QOwnNotes.

When using `--global-resource-folder FOLDER`, the resources are stored relative to the output folder. This means the resources of all files are stored in the same folder. This folder can be also outside of the root folder. Like `../assets` in Logseq.
