# Welcome to jimmy's documentation!

**jimmy** is a tool to import your notes from different formats to markdown.

## Installation

**Download jimmy here: [Linux](https://github.com/marph91/jimmy/releases/latest/download/jimmy-cli-linux) | [Windows](https://github.com/marph91/jimmy/releases/latest/download/jimmy-cli-windows.exe) | [MacOS](https://github.com/marph91/jimmy/releases/latest/download/jimmy-cli-darwin)**

!!! note

    The MacOS app is untested.

Alternative installation options:

1. CLI app: `jimmy-cli-*`. Available at the [release page](https://github.com/marph91/jimmy/releases/latest).
2. Clone the repository and use it from python by `python src/jimmy_cli.py`.
3. GUI app (experimental). Can be used from python `python src/jimmy_gui.py` or built manually by `python -m PyInstaller jimmy_gui.spec`.

## Quickstart

1. [Import from text files](./formats/default.md) or import from specific apps, like [Google Keep](./formats/google_keep.md)
2. Verify that everything was converted properly. The markdown notes should be available in a new folder named like `YYYY-MM-DD HH:MM:SS - Jimmy Import`.
