This page describes how to import notes from Google Keep to Joplin.

## General Information

- [Website](https://keep.google.com/)
- Typical extensions: `.zip`, `.tgz`

## Instructions

1. Export via Takeout as described in <https://www.howtogeek.com/694042/how-to-export-your-google-keep-notes-and-attachments/>
2. [Install jimmy](../index.md#installation)
3. Import to Joplin. Examples:
    1. `jimmy-cli-linux takeout-20240401T160516Z-001.zip --format google_keep`
    2. `jimmy-cli-linux takeout-20240401T160556Z-001.tgz --format google_keep`
