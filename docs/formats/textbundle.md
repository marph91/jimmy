This page describes how to convert notes from Textbundle to Markdown.

## General Information

- [Website](http://textbundle.org/)
- Typical extensions: `.textbundle`, `.textpack` or folder of `.textbundle` and `.textpack`

## Apps that support Textbundle export

Selection from [the textbundle website](http://textbundle.org/#supporting-apps):

- Bear
- Craft
- Ulysses
- Wordpress
- Zettlr

## Instructions

1. Export from any of the mentioned apps
2. [Install jimmy](../index.md#installation)
3. Convert to Markdown. Examples:
    1. `jimmy-cli-linux "Textbundle Example v1.textbundle/" --format textbundle`
    2. `jimmy-cli-linux "example.textpack" --format textbundle`
    3. `jimmy-cli-linux folder/with/textbundles/ --format textbundle`
4. [Import to your app](../import_instructions.md)
