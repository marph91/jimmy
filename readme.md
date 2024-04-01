# joplin-universal-importer

Import your data to Joplin.

:exclamation: Should only be used if the built-in import of Joplin doesn't work.

## Why Joplin's data API is used?

- Plain markdown: Tags aren't supported: <https://discourse.joplinapp.org/t/import-tags-from-markdown-files/1752>
- JEX: Requires to work with some internals that I would rather not touch.
- Joplin's data API: Straight forward to use and supports all needed functions.
