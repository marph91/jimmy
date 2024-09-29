# jimmy

Free your notes by converting them to Markdown.

For detailed information, take a look at the [Documentation](https://marph91.github.io/jimmy/).

If this app is useful for you, feel free to star it on [github](https://github.com/marph91/jimmy).

[![build](https://github.com/marph91/jimmy/actions/workflows/build.yml/badge.svg)](https://github.com/marph91/jimmy/actions/workflows/build.yml)
[![lint](https://github.com/marph91/jimmy/actions/workflows/lint.yml/badge.svg)](https://github.com/marph91/jimmy/actions/workflows/lint.yml)
[![tests](https://github.com/marph91/jimmy/actions/workflows/tests.yml/badge.svg)](https://github.com/marph91/jimmy/actions/workflows/tests.yml)

## Features

- ✅ Many input formats, like Google Keep, Standard Notes, Synology Note Station, Zoho Notebook and more
- ✅ Markdown + Frontmatter output
    - Compatible with any text editor
    - Can be imported to Joplin/Obsidian/...
    - Preserves resources, tags and note links when possible
- ✅ Offline
- ✅ Open Source
- ✅ Cross-platform
- ✅ Standalone (no python or node installation required)

## General Usage

```mermaid
flowchart LR
    A[App 1] -->|Backup| M
    B[App 2] -->|Export| M
    C[...] --> M
    D[Filesystem] --> M
    M(ZIP archive/JSON/Folder) --> N
    N{jimmy} --> O(Markdown + Frontmatter)
    O -->|Import| P[Joplin]
    O -->|Import| Q[Obsidian]
    O --> R[...]
    O --> S[Editor, e. g. VSCode]
```

1. Export/backup notes from your note application
2. Run `jimmy`, which converts your notes to Markdown
3. Import the result to Joplin/Obsidian or use any editor to view the notes

For detailed instructions, see the page of the [specific format](https://marph91.github.io/jimmy/formats/default/).

## Quickstart

1. Download jimmy here: [**Linux**](https://github.com/marph91/jimmy/releases/latest/download/jimmy-cli-linux) | [**Windows**](https://github.com/marph91/jimmy/releases/latest/download/jimmy-cli-windows.exe) | [**MacOS**](https://github.com/marph91/jimmy/releases/latest/download/jimmy-cli-darwin) [^macos]
2. Examples for the Linux CLI app:

```bash
# import a single file supported by pandoc
jimmy-cli-linux libre_office_document.odt

# import all files in a folder
jimmy-cli-linux path/to/folder

# import a Google Keep export
jimmy-cli-linux takeout-20240401T160516Z-001.zip --format google_keep
```

After conversion, the notes should be available in a folder named like `YYYY-MM-DD HH:MM:SS - Import`. Make sure your data is converted properly :exclamation:

What is converted (in most cases)?

- Note content
- Tags / Labels
- Images / Resources / Attachments
- External links and internal note links

If something is not working, please check the issues first. If you can't find anything, feel free to create a new issue. It might be just not implemented yet or a regression. On the other side, the exported data can be sparse. In that case it's not possible to transfer the data with jimmy.

[^macos]: The MacOS app is untested.

## Demo

This is an example of a successful conversion:

```bash
$ jimmy-cli-linux .cache/google_keep/takeout-20240401T160516Z-001.zip --format google_keep --frontmatter joplin
[09/19/24 15:15:34] INFO     Importing notes from ".cache/google_keep/takeout-20240401T160516Z-001.zip"
                    INFO     Start parsing
                    INFO     Finished parsing: 1 notebooks, 3 notes, 1 resources, 3 tags
                    INFO     Start filtering
                    INFO     Finished filtering: 1 notebooks, 3 notes, 1 resources, 3 tags
                    INFO     Start writing to file system
                    INFO     Converted notes successfully to Markdown: "20240919T131534Z - Jimmy Import from google_keep". Please verify that everything was converted correctly.
                    INFO     Feel free to open an issue on Github, write a message at the Joplin forum or an email.

Notebooks  100%|████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00]
Notes      100%|████████████████████████████████████████████████████████████████████| 3/3 [00:00<00:00]
Resources  100%|████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00]
Tags       100%|████████████████████████████████████████████████████████████████████| 3/3 [00:00<00:00]
```

## Similar Projects

- [Obsidian-Importer](https://github.com/obsidianmd/obsidian-importer)
- [YANOM-Note-O-Matic (fork)](https://github.com/stereohorse/YANOM-Note-O-Matic)
