# Welcome to jimmy's documentation!

**jimmy** is a tool to import your notes from different formats to Joplin.

## Installation

**Download jimmy here: [Linux](https://github.com/marph91/jimmy/releases/latest/download/jimmy-cli-linux) | [Windows](https://github.com/marph91/jimmy/releases/latest/download/jimmy-cli-windows.exe) | [MacOS](https://github.com/marph91/jimmy/releases/latest/download/jimmy-cli-darwin)**

!!! note

    The MacOS app is untested.

Alternative installation options:

1. CLI app: `jimmy-cli-*`. Available at the [release page](https://github.com/marph91/jimmy/releases/latest).
2. Clone the repository and use it from python by `python src/jimmy_cli.py`.
3. GUI app (experimental). Can be used from python `python src/jimmy_gui.py` or built manually by `python -m PyInstaller jimmy_gui.spec`.

## Quickstart

1. This script requires that the webclipper in Joplin is running. It will connect to Joplin at the first execution.
2. [Import from text files](./formats/default.md) or import from specific apps, like [Google Keep](./formats/google_keep.md)
3. Verify that everything was imported properly. The imported notes should be available in a new Joplin notebook named like `YYYY-MM-DD HH:MM:SS - Import`.
