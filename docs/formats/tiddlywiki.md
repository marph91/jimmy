This page describes how to convert notes from TiddlyWiki to Markdown.

## General Information

- [Website](https://tiddlywiki.com/)
- Typical extension: `.json`

## Instructions

1. Export as described [at the website](https://tiddlywiki.com/static/How%2520to%2520export%2520tiddlers.html)
    1. Choose json export
2. [Install jimmy](../index.md#installation)
3. Convert to Markdown. Example: `jimmy-cli-linux tiddlers.json --format tiddlywiki`
4. [Import to your app](../import_instructions.md)

## Known Limitations

Note content is in TiddlyWiki's [WikiText format](https://tiddlywiki.com/#WikiText). It is converted, but Markdown supports only a subset.
