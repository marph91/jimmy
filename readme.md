# jimmy

Tool to import your notes to Joplin.

:exclamation: Should only be used if the built-in import of Joplin isn't available for your note format.

For detailed information, take a look at the [Documentation](https://marph91.github.io/jimmy/).

If this app is useful for you, feel free to star it on [github](https://github.com/marph91/jimmy).

[![build](https://github.com/marph91/jimmy/actions/workflows/build.yml/badge.svg)](https://github.com/marph91/jimmy/actions/workflows/build.yml)
[![lint](https://github.com/marph91/jimmy/actions/workflows/lint.yml/badge.svg)](https://github.com/marph91/jimmy/actions/workflows/lint.yml)
[![tests](https://github.com/marph91/jimmy/actions/workflows/tests.yml/badge.svg)](https://github.com/marph91/jimmy/actions/workflows/tests.yml)

## Quickstart

1. Download jimmy here: [Linux](https://github.com/marph91/jimmy/releases/latest/download/jimmy-cli-linux) | [Windows](https://github.com/marph91/jimmy/releases/latest/download/jimmy-cli-windows.exe) | [MacOS](https://github.com/marph91/jimmy/releases/latest/download/jimmy-cli-darwin) [^macos]
2. This script requires that the webclipper in Joplin is running. It will connect to Joplin at the first execution.
3. Examples for the Linux CLI app:

```bash
# import a single file supported by pandoc
jimmy-cli-linux libre_office_document.odt

# import all files in a folder
jimmy-cli-linux path/to/folder

# import a Google Keep export
jimmy-cli-linux takeout-20240401T160516Z-001.zip --format google_keep
```

After importing, the notes should be available in a new Joplin notebook named like `YYYY-MM-DD HH:MM:SS - Import`.

:exclamation: Make sure your data is imported properly.

What is converted (in most cases)?

- Note content
- Metadata
- Tags / Labels
- Resources / Attachments
- Images
- External links and internal note links
- Markdown Front Matter

If something is not working, please check the issues first. If you can't find anything, feel free to create a new issue. It might be just not implemented yet or a regression. On the other side, the exported data can be sparse. In that case it's not possible to transfer the data with jimmy.

[^macos]: The MacOS app is untested.

## Demo

<https://github.com/marph91/jimmy/assets/33229141/de8f8e96-f925-4eef-8ff3-f69b5ee067ef>

## Similar Projects

- [Obsidian-Importer](https://github.com/obsidianmd/obsidian-importer)
