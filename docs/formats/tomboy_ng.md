---
description: Convert from Tomboy-ng to Markdown.
---

# Convert from Tomboy-ng to Markdown

## General Information

- [Tomboy-ng Website](https://github.com/tomboy-notes/tomboy-ng)
- [Gnote Website](https://wiki.gnome.org/Apps/Gnote). Gnote is a [port of Tomboy to C++](https://askubuntu.com/a/77046/641874). They use a similar note format.
- Typical extension: `.note` file or folder with `.note` files

## Instructions

1. [Install Jimmy](../index.md#installation)
2. Convert to Markdown. Examples:
    1. `jimmy-cli-linux ~/.local/share/tomboy-ng/ --format tomboy_ng`
    2. `jimmy-cli-linux ~/.local/share/gnote --format tomboy_ng`
    3. `jimmy-cli-linux tomboy-ng/5E74990A-E93E-4A11-AEA2-0814A37FEE1A.note --format tomboy_ng`
3. [Import to your app](../import_instructions.md)

## Known Limitations

- Note links are not exported.
- Multiple formats are not converted properly.
