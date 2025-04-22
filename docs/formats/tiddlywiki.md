---
source_app: TiddlyWiki
---

# Convert from TiddlyWiki to Markdown

## General Information

- [Website](https://tiddlywiki.com/)
- Typical extension: `.json`, `.tid` or folder of `.tid` files

## Instructions

1. Export as described [at the website](https://tiddlywiki.com/#How%20to%20export%20tiddlers)
    1. Choose "JSON file" if you want to export the complete wiki
    2. Choose "TID text file" if you want to export a single tiddler only. Resources and internal links won't be converted in this case.
2. [Install Jimmy](../index.md#installation)
3. Convert to Markdown. Examples:
    1. `jimmy-cli-linux tiddlers.json --format tiddlywiki`
    2. `jimmy-cli-linux tiddlers.tid --format tiddlywiki`
    3. `jimmy-cli-linux /folder/to/tiddlers --format tiddlywiki`
4. [Import to your app](../import_instructions.md)

## Known Limitations

Note content is in TiddlyWiki's [WikiText format](https://tiddlywiki.com/#WikiText). It is converted, but Markdown supports only a subset. For example JavaScript functions won't work in the converted Markdown anymore.
