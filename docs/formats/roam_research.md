# Convert from Roam Research to Markdown

## General Information

- [Website](https://roamresearch.com/)
- Typical extension: `.json`

## Instructions

1. Export as described [at the website](https://help.roam.garden/How-to-export-your-Roam-Graph)
    1. Choose "Export All" -> "JSON"
2. [Install Jimmy](../index.md#installation)
3. Convert to Markdown. Example `jimmy-cli-linux export.edn --format roam_research`
4. [Import to your app](../import_instructions.md)

## Known Limitations

- Block links are converted to page links.
- Embedded pages and blocks are converted to links.
