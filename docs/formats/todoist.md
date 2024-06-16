- [Website](https://todoist.com/)
- Typical extension: `.csv`

## Export instructions

- <https://todoist.com/de/help/articles/introduction-to-backups-ywaJeQbN>
- Uncheck "Use relative data" when exporting.

## Import to Joplin

Example: `jimmy-cli-linux Privates.csv --format todoist`

## Known Limitations

- Finished todo's are not exported at all.
- Subtasks are converted to regular notes. I. e. they lose their indentation.
- Markdown is not rendered in note titles.
