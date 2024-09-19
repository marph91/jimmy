This page describes how to convert notes from Todoist to Markdown.

## General Information

- [Website](https://todoist.com/)
- Typical extension: `.csv`

## Instructions

1. Export as described in <https://todoist.com/de/help/articles/introduction-to-backups-ywaJeQbN>
    1. Uncheck "Use relative data" when exporting.
2. [Install jimmy](../index.md#installation)
3. Convert to Markdown. Example: `jimmy-cli-linux Privates.csv --format todoist`
4. [Import to your app](../import_instructions.md)

## Known Limitations

- Finished todo's are not exported at all.
- Subtasks are converted to regular notes. I. e. they lose their indentation.
- Markdown is not rendered in note titles.
