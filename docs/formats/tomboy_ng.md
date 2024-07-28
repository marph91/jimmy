This page describes how to import notes from Tomboy-ng to Joplin.

## General Information

- [Website](https://wiki.gnome.org/Apps/Tomboy/tomboy-ng)
- Typical extension: Folder with `.note` files

## Instructions

1. Export as described in <https://todoist.com/de/help/articles/introduction-to-backups-ywaJeQbN>
    1. Uncheck "Use relative data" when exporting.
2. [Install jimmy](../index.md#installation)
3. Import to Joplin. Examples:
    1. `jimmy-cli-linux ~/.local/share/tomboy-ng/ --format tomboy_ng`
    2. `jimmy-cli-linux tomboy-ng/5E74990A-E93E-4A11-AEA2-0814A37FEE1A.note --format tomboy_ng`

## Known Limitations

- Note links are not exported.
- Multiple formats are not converted properly.
