This page describes how to import notes from TiddlyWiki to Joplin.

## General Information

- [Website](https://tiddlywiki.com/)
- Typical extension: `.json`

## Instructions

1. Export as described in <https://tiddlywiki.com/static/How%2520to%2520export%2520tiddlers.html>
    1. Choose json export
2. [Install jimmy](../index.md#installation)
3. Import to Joplin. Example: `jimmy-cli-linux tiddlers.json --format tiddlywiki`

## Known Limitations

Note content is imported in TiddlyWiki's [WikiText format](https://tiddlywiki.com/#WikiText) and not converted to markdown.
