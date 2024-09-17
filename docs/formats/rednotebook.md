This page describes how to import notes from RedNotebook to markdown.

## General Information

- [Website](https://rednotebook.app/)
- Typical extension: `.zip` or data folder with text files

## Instructions

1. Create a backup of your notes as described [here](https://rednotebook.app/help.html#toc13) or specify the data folder (for example `$HOME/.rednotebook/data`)
2. [Install jimmy](../index.md#installation)
3. Convert to markdown. Examples:
   1. `jimmy-cli-linux RedNotebook-Backup-2024-09-15.zip --format rednotebook`
   2. `jimmy-cli-linux ~/.rednotebook/data/ --format rednotebook`

## Known Limitations

Images and files are not part of the backup. They will only be included, if the files exist in your filesystem.
