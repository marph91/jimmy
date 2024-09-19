This page describes how to convert notes from Tomboy-ng and Gnote to Markdown.

## General Information

- [Tomboy-ng Website](https://wiki.gnome.org/Apps/Tomboy/tomboy-ng)
- [Gnote Website](https://wiki.gnome.org/Apps/Gnote)
- Typical extension: `.note` file or folder with `.note` files

## Instructions

1. [Install jimmy](../index.md#installation)
2. Convert to Markdown. Examples:
    1. `jimmy-cli-linux ~/.local/share/tomboy-ng/ --format tomboy_ng`
    2. `jimmy-cli-linux ~/.local/share/gnote --format tomboy_ng`
    3. `jimmy-cli-linux tomboy-ng/5E74990A-E93E-4A11-AEA2-0814A37FEE1A.note --format tomboy_ng`

## Known Limitations

- Note links are not exported.
- Multiple formats are not converted properly.
