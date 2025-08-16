---
source_app: Textbundle
---

# Convert from Textbundle to Markdown

## General Information

- [Website](http://textbundle.org/)
- Typical extensions: `.textbundle`, `.textpack` or folder of `.textbundle` and `.textpack`

## Apps that support Textbundle export

Selection from [the textbundle website](http://textbundle.org/#supporting-apps):

- Bear
- Craft
- Ulysses
- WordPress
- Zettlr

## Instructions

1. Export from any of the mentioned apps
2. [Install Jimmy](../index.md#installation)
3. Convert to Markdown. Examples:
    1. `jimmy-linux cli "Textbundle Example v1.textbundle/" --format textbundle`
    2. `jimmy-linux cli "example.textpack" --format textbundle`
    3. `jimmy-linux cli folder/with/textbundles/ --format textbundle`
4. [Import to your app](../import_instructions.md)
