# joplin-custom-importer

Import your data to Joplin.

:exclamation: Should only be used if the built-in import of Joplin doesn't work.

## Supported formats and apps

Every format that is supported by pandoc. Some formats may need some tweaking, though.

| App | Notes | Tags | Resources | Internal Name | Export Instructions |
| --- | --- | --- | --- | --- | --- |
| [clipto](https://clipto.pro/) | ✅   | ✅   | -  | clipto | [mobile only](https://github.com/clipto-pro/Desktop/issues/21#issuecomment-537401330) |
| [Google Keep](https://keep.google.com) | ✅   | ✅   | ✅   | google_keep | [via Takeout](https://www.howtogeek.com/694042/how-to-export-your-google-keep-notes-and-attachments/) |

## Usage

This script requires that the webclipper in Joplin is running. It will connect to Joplin at the first execution.

```bash
# import a single file supported by pandoc
joplin_custom_importer libre_office_document.odt

# import all files in a folder
joplin_custom_importer path/to/folder

# import a clipto export
joplin_custom_importer clipto_backup_240401_105154.json --app clipto

# import a Google Keep export
joplin_custom_importer takeout-20240401T160516Z-001.zip --app google_keep
```

After importing, the notes should be available in a new Joplin notebook named like `YYYY-MM-DD HH:MM:SS - Import`.

## Why Joplin's data API is used?

- Plain markdown: Tags aren't supported: <https://discourse.joplinapp.org/t/import-tags-from-markdown-files/1752>
- JEX: Requires to work with some internals that I would rather not touch.
- Joplin's data API: Straight forward to use and supports all needed functions.
