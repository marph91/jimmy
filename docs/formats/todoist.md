This page describes how to import notes from Todoist to Joplin.

## General Information

- [Website](https://todoist.com/)
- Typical extension: `.csv`

## Instructions

1. Export as described in <https://todoist.com/de/help/articles/introduction-to-backups-ywaJeQbN>
    1. Uncheck "Use relative data" when exporting.
2. [Install jimmy](../index.md#Installation)
3. Import to Joplin. Example: `jimmy-cli-linux Privates.csv --format todoist`

## Known Limitations

- Finished todo's are not exported at all.
- Subtasks are converted to regular notes. I. e. they lose their indentation.
- Markdown is not rendered in note titles.
