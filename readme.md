# joplin-custom-importer

Simple tool to import your data to Joplin.

:exclamation: Should only be used if the built-in import of Joplin doesn't work.

:exclamation: Make sure your data is imported properly after the script finished.

## Usage

This script requires that the webclipper in Joplin is running. It will connect to Joplin at the first execution.

Grab the executable from the [build workflow](https://github.com/marph91/joplin-custom-importer/actions/workflows/build.yml).

```bash
# import a single file supported by pandoc
joplin_custom_importer libre_office_document.odt

# import multiple files
joplin_custom_importer plaintext.txt markdown.md

# import all files in a folder
joplin_custom_importer path/to/folder

# import a clipto export
joplin_custom_importer clipto_backup_240401_105154.json --app clipto

# import a Google Keep export
joplin_custom_importer takeout-20240401T160516Z-001.zip --app google_keep
```

After importing, the notes should be available in a new Joplin notebook named like `YYYY-MM-DD HH:MM:SS - Import`.

## Supported Formats

- Every format that is supported by pandoc. Some formats may need some tweaking, though.
- txt

## Supported Apps

| App | Internal App Name | Export Instructions |
| --- | --- | --- |
| [clipto](https://clipto.pro/) | clipto | [mobile only](https://github.com/clipto-pro/Desktop/issues/21#issuecomment-537401330) |
| [Google Keep](https://keep.google.com) | google_keep | [via Takeout](https://www.howtogeek.com/694042/how-to-export-your-google-keep-notes-and-attachments/) |
| [Nimbus Note / FuseBase](https://nimbusweb.me/note/) | nimbus_note | [link](https://nimbusweb.me/guides/settings/how-to-export-notes-to-html-or-pdf/) |
| [Simplenote](https://simplenote.com/) | simplenote | [link](https://simplenote.com/help/#export) |
| [TiddlyWiki](https://tiddlywiki.com/) | tiddlywiki | [JSON only](https://tiddlywiki.com/static/How%2520to%2520export%2520tiddlers.html) [1] |

[1] Note content is imported in TiddlyWiki's [WikiText format](https://tiddlywiki.com/#WikiText) and not converted to markdown.

There are many more apps supported implicitly if they export text files to a folder. Just specify the folder and try the import (see [usage](#usage)).

What is migrated?

- Notes and their content
- Tags / Labels
- Resources / Attachments
- Creation and modification date

What is not handled (yet)?

- Internal note links
- Markdown Front Matter
- Inline tags

If something else is not working, please check the issues first. If you can't find anything, feel free to create a new issue. It might be just not implemented yet or a regression. On the other side, the exported data can be sparse. In that case it's not possible to transfer the data with this tool.

## Why Joplin's data API is used?

- Plain markdown: [Tags aren't supported](https://discourse.joplinapp.org/t/import-tags-from-markdown-files/1752).
- JEX: Requires to work with some internals that I would rather not touch.
- Joplin's data API: Straight forward to use and supports all needed functions.
