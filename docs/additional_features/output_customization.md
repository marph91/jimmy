---
description: This page describes how to customize the Markdown output of Jimmy.
---

The output can be customized in the following ways.

## Front Matter

Include Markdown front matter by `--frontmatter`. Currently, Joplin and Obsidian compatible front matter (`--frontmatter joplin` respectively `--frontmatter obsidian`) can be generated.

## Output Folder

The output folder can be specified by `--output-folder OUTPUT_FOLDER`.

## Resource Location

Resources are stored by default next to the Markdown file. When using `--local-resource-folder FOLDER`, the resources are stored relative to the Markdown files. For example in an `media` folder, like in QOwnNotes.

When using `--global-resource-folder FOLDER`, the resources are stored relative to the output folder. This means the resources of all files are stored in the same folder. This folder can be also outside the root folder. Like `../assets` in Logseq.
