This page describes how to convert notes from Toodledo to Markdown.

## General Information

- [Website](https://www.toodledo.com/)
- Typical extension: `.csv`

## Instructions

1. Export as described in <https://www.toodledo.com/tools/import_export.php>
    1. Uncheck "Use relative data" when exporting.
2. [Install jimmy](../index.md#installation)
3. Convert to Markdown. Examples:
    1. `jimmy-cli-linux toodledo_completed_240427.csv --format toodledo`
    2. `jimmy-cli-linux toodledo_current_240427.csv --format toodledo`
    3. `jimmy-cli-linux toodledo_notebook_240427.csv --format toodledo`

## Known Limitations

[subtasks](https://www.toodledo.com/info/subtasks.php) and [files](https://www.toodledo.com/organize/files.php) are not implemented, since they require a subscription.
