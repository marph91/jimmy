---
source_app: Signal
---

# Convert from Signal to Markdown

## General Information

- [Website](https://signal.org/)
- Typical extension: Folder with a `config.json` file and all kinds of Signal data

## Instructions

1. [Install Jimmy](../index.md#installation)
2. Convert to Markdown. Example: `jimmy-linux cli /home/user/.config/Signal/ --format signal`
3. [Import to your app](../import_instructions.md)

### Typical Location of the Signal Data

| Operating System | Typical Location |
| --- | --- |
| Windows | `C:\Users\<YourName>\AppData\Roaming\Signal` |
| macOS | `~/Library/Application Support/Signal` |
| Linux | `~/.config/Signal` |

## Compatibility

| Feature | Supported? | Remark |
| --- | :---: | --- |
| Attachments / Images / Resources | ✅ | |
| Labels / Tags | ⬜ | |
| Note Links | ⬜ | |
| Notebook / Folder Hierarchy | ⬜ | |
| Rich Text | ✅ | |

## Acknowledgements

This converter is based on [signal-export](https://github.com/carderne/signal-export/). Thanks for developing it!
