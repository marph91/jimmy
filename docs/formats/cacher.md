- [Website](https://www.cacher.io/)
- Typical extension: `.json`

## Export instructions

<https://www.cacher.io/docs/guides/snippets/exporting-snippets#how-to-export-1>

## Import to Joplin

Example: `jimmy-cli-linux cacher-export-202406182304.json --format cacher`

## Import structure

- Cacher labels are converted to Joplin tags.
- Cacher snippets are converted to Joplin notebooks.
- Cacher files are converted to Joplin notes.

## Known limitations

- Only markdown files are converted for now.
- Files attached to snippets are not exported.
