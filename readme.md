![Jimmy logo](./docs/images/logo2.png)

Free your notes by converting them to Markdown.

:floppy_disk: Download: [**Linux**](https://github.com/marph91/jimmy/releases/latest/download/jimmy-cli-linux) | [**Windows**](https://github.com/marph91/jimmy/releases/latest/download/jimmy-cli-windows.exe) | [**macOS**](https://github.com/marph91/jimmy/releases/latest/download/jimmy-cli-darwin-arm64) [![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/marph91/jimmy/total)](https://hanadigital.github.io/grev/?user=marph91&repo=jimmy)

If there is an issue at download or execution, please take a look at the [step-by-step instructions](#step-by-step-instructions).

:blue_book: For detailed information, take a look at the [Documentation](https://marph91.github.io/jimmy/).

:star: If Jimmy is useful for you, feel free to star it on [GitHub](https://github.com/marph91/jimmy).

[![build](https://github.com/marph91/jimmy/actions/workflows/build.yml/badge.svg)](https://github.com/marph91/jimmy/actions/workflows/build.yml)
[![lint](https://github.com/marph91/jimmy/actions/workflows/lint.yml/badge.svg)](https://github.com/marph91/jimmy/actions/workflows/lint.yml)
[![tests](https://github.com/marph91/jimmy/actions/workflows/tests.yml/badge.svg)](https://github.com/marph91/jimmy/actions/workflows/tests.yml)

## Use Cases

- Migrate between note apps
- Save your notes in a future-proof, human-readable format
- Prepare your notes for processing in a LLM

## Demo

Example commands for the Linux CLI app:

```bash
# convert a single file supported by pandoc
jimmy-cli-linux libre_office_document.odt

# convert all files in a folder
jimmy-cli-linux path/to/folder

# convert a Google Keep export
jimmy-cli-linux takeout-20240401T160516Z-001.zip --format google_keep
```

This is an example of a successful conversion:

https://github.com/user-attachments/assets/dcd2bc5e-2442-468e-a792-5def563c6981

## Features

- ✅ Several supported input formats
- ✅ Markdown + Front matter output
    - Compatible with any text editor
    - Can be imported to Joplin/Obsidian/...
    - Preserves resources, tags and note links when possible
- ✅ Offline
- ✅ Open Source
- ✅ Cross-platform
- ✅ Standalone (no Docker, Python or Node.js installation required)
- ❎ No AI

## Supported Apps

Export data from your app and convert it to Markdown. For details, click on the links.

`A` <img alt="Anki logo" src="https://upload.wikimedia.org/wikipedia/commons/thumb/3/3d/Anki-icon.svg/240px-Anki-icon.svg.png" style="height:20px;max-width:20px;"> [Anki](https://marph91.github.io/jimmy/formats/anki/) <img alt="Anytype logo" src="https://raw.githubusercontent.com/anyproto/anytype-ts/f5bad768813c6e8b783192adfd25c7410494977c/src/img/logo/symbol.svg" style="height:20px;max-width:20px;"> [Anytype](https://marph91.github.io/jimmy/formats/anytype/)
`B` <img alt="Bear logo" src="https://bear.app/images/logo.png" style="height:20px;max-width:20px;"> [Bear](https://marph91.github.io/jimmy/formats/bear/)
`C` <img alt="Cacher logo" src="https://raw.githubusercontent.com/CacherApp/cacher-cli/e241f06867dba740131db5314ef7fe279135baf6/images/cacher-icon.png" style="height:20px;max-width:20px;"> [Cacher](https://marph91.github.io/jimmy/formats/cacher/) <img alt="CherryTree logo" src="https://raw.githubusercontent.com/giuspen/cherrytree/c822b16681b002b8882645d8d1e8f109514ddb58/icons/cherrytree.svg" style="height:20px;max-width:20px;"> [CherryTree](https://marph91.github.io/jimmy/formats/cherrytree/) <img alt="Clipto logo" src="https://avatars.githubusercontent.com/u/53916365?s=200&v=4" style="height:20px;max-width:20px;"> [Clipto](https://marph91.github.io/jimmy/formats/clipto/) <img alt="ColorNote logo" src="https://www.colornote.com/wp-content/uploads/2016/05/cropped-favicon.png" style="height:20px;max-width:20px;"> [ColorNote](https://marph91.github.io/jimmy/formats/colornote/)
`D` <img alt="Day One logo" src="https://iconape.com/wp-content/files/rb/342127/png/day-one-logo.png" style="height:20px;max-width:20px;"> [Day One](https://marph91.github.io/jimmy/formats/day_one/) <img alt="Drafts logo" src="https://getdrafts.com/assets/favicon/favicon.ico" style="height:20px;max-width:20px;"> [Drafts](https://marph91.github.io/jimmy/formats/drafts/) <img alt="Dynalist logo" src="https://images.saasworthy.com/dynalist_5288_logo_1576239391_xhkcg.jpg" style="height:20px;max-width:20px;"> [Dynalist](https://marph91.github.io/jimmy/formats/dynalist/)
`E` <img alt="Evernote logo" src="https://avatars.githubusercontent.com/u/1120885" style="height:20px;max-width:20px;"> [Evernote](https://marph91.github.io/jimmy/formats/evernote/)
`F` <img alt="Facebook logo" src="https://upload.wikimedia.org/wikipedia/commons/b/b8/2021_Facebook_icon.svg" style="height:20px;max-width:20px;"> [Facebook](https://marph91.github.io/jimmy/formats/facebook/) <img alt="FuseBase logo" src="https://wavebox.pro/store2/store/0b46bf0a-107c-4fa2-a657-3df7412e3d3d.png" style="height:20px;max-width:20px;"> [FuseBase / Nimbus Note](https://marph91.github.io/jimmy/formats/nimbus_note/)
`G` <img alt="Google Docs logo" src="https://www.gstatic.com/images/branding/product/1x/docs_2020q4_96dp.png" style="height:20px;max-width:20px;"> [Google Docs](https://marph91.github.io/jimmy/formats/google_docs/) <img alt="Google Keep logo" src="https://www.gstatic.com/images/branding/product/1x/keep_2020q4_96dp.png" style="height:20px;max-width:20px;"> [Google Keep](https://marph91.github.io/jimmy/formats/google_keep/)
`J` <img alt="Joplin logo" src="https://github.com/laurent22/joplin/blob/dev/Assets/LinuxIcons/128x128.png?raw=true" style="height:20px;max-width:20px;"> [Joplin](https://marph91.github.io/jimmy/formats/joplin/) <img alt="jrnl logo" src="https://raw.githubusercontent.com/jrnl-org/jrnl/85a98afcd91ed873c0eceba9893c3ec424f201b8/docs_theme/img/logo.svg" style="height:20px;max-width:20px;"> [jrnl](https://marph91.github.io/jimmy/formats/jrnl/)
`N` <img alt="Notion logo" src="https://upload.wikimedia.org/wikipedia/commons/4/45/Notion_app_logo.png" style="height:20px;max-width:20px;"> [Notion](https://marph91.github.io/jimmy/formats/notion/)
`O` <img alt="Obsidian logo" src="https://upload.wikimedia.org/wikipedia/commons/1/10/2023_Obsidian_logo.svg" style="height:20px;max-width:20px;"> [Obsidian](https://marph91.github.io/jimmy/formats/obsidian/)
`Q` <img alt="QOwnNotes logo" src="https://raw.githubusercontent.com/pbek/QOwnNotes/d89a597a28eeb16f57692ac121933b478f44bf07/src/images/icons/256x256/apps/QOwnNotes.png" style="height:20px;max-width:20px;"> [QOwnNotes](https://marph91.github.io/jimmy/formats/qownnotes/)
`R` <img alt="RedNotebook logo" src="https://raw.githubusercontent.com/jendrikseipp/rednotebook/b2cefe5f321b21ab7ad855059f3c0496eb0830d2/rednotebook/images/rednotebook-icon/rn-256.png" style="height:20px;max-width:20px;"> [RedNotebook](https://marph91.github.io/jimmy/formats/rednotebook/) <img alt="Roam Research logo" src="https://upload.wikimedia.org/wikipedia/commons/6/61/Astrolabe-black.png" style="height:20px;max-width:20px;"> [Roam Research](https://marph91.github.io/jimmy/formats/roam_research/)
`S` <img alt="Simplenote logo" src="https://raw.githubusercontent.com/Automattic/simplenote-electron/4a140a96545763c849b26a81a2e27ff67eaa68f0/lib/icons/app-icon/icon_256x256.png" style="height:20px;max-width:20px;"> [Simplenote](https://marph91.github.io/jimmy/formats/simplenote/) <img alt="Standard Notes logo" src="https://avatars.githubusercontent.com/u/24537496?s=100" style="height:20px;max-width:20px;"> [Standard Notes](https://marph91.github.io/jimmy/formats/standard_notes/) <img alt="Synology Note Station logo" src="https://www.synology.com/img/dsm/note_station/notestation_72.png" style="height:20px;max-width:20px;"> [Synology Note Station](https://marph91.github.io/jimmy/formats/synology_note_station/)
`T` <img alt="Telegram logo" src="https://upload.wikimedia.org/wikipedia/commons/8/82/Telegram_logo.svg" style="height:20px;max-width:20px;"> [Telegram](https://marph91.github.io/jimmy/formats/tiddlywiki/) <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 384 512" style="height:20px;max-width:20px;" fill="gray" opacity="0.5"><!--!Font Awesome Free 6.7.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2025 Fonticons, Inc.--><path d="M64 464c-8.8 0-16-7.2-16-16L48 64c0-8.8 7.2-16 16-16l160 0 0 80c0 17.7 14.3 32 32 32l80 0 0 288c0 8.8-7.2 16-16 16L64 464zM64 0C28.7 0 0 28.7 0 64L0 448c0 35.3 28.7 64 64 64l256 0c35.3 0 64-28.7 64-64l0-293.5c0-17-6.7-33.3-18.7-45.3L274.7 18.7C262.7 6.7 246.5 0 229.5 0L64 0zm56 256c-13.3 0-24 10.7-24 24s10.7 24 24 24l144 0c13.3 0 24-10.7 24-24s-10.7-24-24-24l-144 0zm0 96c-13.3 0-24 10.7-24 24s10.7 24 24 24l144 0c13.3 0 24-10.7 24-24s-10.7-24-24-24l-144 0z"/></svg> [Textbundle / Textpack](https://marph91.github.io/jimmy/formats/textbundle/) <img alt="Tiddlywiki logo" src="https://talk.tiddlywiki.org/uploads/default/original/1X/5d4e8afa05b64280281f851dfc982796b5f7fcd1.svg" style="height:20px;max-width:20px;"> [Tiddlywiki](https://marph91.github.io/jimmy/formats/tiddlywiki/) <img alt="Tomboy-ng logo" src="https://dl.flathub.org/media/org/gnome/Gnote/4f2ede31f33a5f935bec4206a6035410/icons/128x128/org.gnome.Gnote.png" style="height:20px;max-width:20px;"> [Tomboy-ng / Gnote](https://marph91.github.io/jimmy/formats/tomboy_ng/) <img alt="Turtl logo" src="https://turtlapp.com/images/logo.svg" style="height:20px;max-width:20px;"> [Turtl](https://marph91.github.io/jimmy/formats/turtl/)
`W` <img alt="Wordpress logo" src="https://s.w.org/style/images/about/WordPress-logotype-wmark.png" style="height:20px;max-width:20px;"> [Wordpress](https://marph91.github.io/jimmy/formats/wordpress/)
`Z` <img alt="Zettelkasten logo" src="https://raw.githubusercontent.com/Zettelkasten-Team/Zettelkasten/refs/heads/main/src/main/resources/de/danielluedecke/zettelkasten/resources/icons/zkn3-256x256.png" style="height:20px;max-width:20px;"> [Zettelkasten](https://marph91.github.io/jimmy/formats/zettelkasten/) <img alt="Zim logo" src="https://zim-wiki.org/images/globe.png" style="height:20px;max-width:20px;"> [Zim](https://marph91.github.io/jimmy/formats/zim/) <img alt="Zoho Notebook logo" src="https://zohowebstatic.com/sites/default/files/ogimage/notebook-logo.png" style="height:20px;max-width:20px;"> [Zoho Notebook](https://marph91.github.io/jimmy/formats/zoho_notebook/)

## Supported Formats

Convert a single file or a folder (recursively). Files of these formats will be converted to Markdown. The formats can be mixed. For example, you can convert a folder with two Asciidoc files and one DOCX file. The conversion result will be a folder with three Markdown files and the corresponding attachments.

`A` <img alt="Asciidoc logo" src="https://avatars.githubusercontent.com/u/3137042?s=100&v=4" style="height:20px;max-width:20px;"> [Asciidoc](https://marph91.github.io/jimmy/formats/default/)
`C` <img alt="CSV logo" src="https://upload.wikimedia.org/wikipedia/commons/3/34/Microsoft_Office_Excel_%282019%E2%80%93present%29.svg" style="height:20px;max-width:20px;"> [CSV](https://marph91.github.io/jimmy/formats/default/)
`D` <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 384 512" style="height:20px;max-width:20px;" fill="gray" opacity="0.5"><!--!Font Awesome Free 6.7.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2025 Fonticons, Inc.--><path d="M64 464c-8.8 0-16-7.2-16-16L48 64c0-8.8 7.2-16 16-16l160 0 0 80c0 17.7 14.3 32 32 32l80 0 0 288c0 8.8-7.2 16-16 16L64 464zM64 0C28.7 0 0 28.7 0 64L0 448c0 35.3 28.7 64 64 64l256 0c35.3 0 64-28.7 64-64l0-293.5c0-17-6.7-33.3-18.7-45.3L274.7 18.7C262.7 6.7 246.5 0 229.5 0L64 0zm56 256c-13.3 0-24 10.7-24 24s10.7 24 24 24l144 0c13.3 0 24-10.7 24-24s-10.7-24-24-24l-144 0zm0 96c-13.3 0-24 10.7-24 24s10.7 24 24 24l144 0c13.3 0 24-10.7 24-24s-10.7-24-24-24l-144 0z"/></svg> [DocBook](https://marph91.github.io/jimmy/formats/default/) <img alt="DOCX logo" src="https://upload.wikimedia.org/wikipedia/commons/f/fd/Microsoft_Office_Word_%282019%E2%80%93present%29.svg" style="height:20px;max-width:20px;"> [DOCX](https://marph91.github.io/jimmy/formats/default/)
`E` <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 384 512" style="height:20px;max-width:20px;" fill="gray" opacity="0.5"><!--!Font Awesome Free 6.7.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2025 Fonticons, Inc.--><path d="M64 464c-8.8 0-16-7.2-16-16L48 64c0-8.8 7.2-16 16-16l160 0 0 80c0 17.7 14.3 32 32 32l80 0 0 288c0 8.8-7.2 16-16 16L64 464zM64 0C28.7 0 0 28.7 0 64L0 448c0 35.3 28.7 64 64 64l256 0c35.3 0 64-28.7 64-64l0-293.5c0-17-6.7-33.3-18.7-45.3L274.7 18.7C262.7 6.7 246.5 0 229.5 0L64 0zm56 256c-13.3 0-24 10.7-24 24s10.7 24 24 24l144 0c13.3 0 24-10.7 24-24s-10.7-24-24-24l-144 0zm0 96c-13.3 0-24 10.7-24 24s10.7 24 24 24l144 0c13.3 0 24-10.7 24-24s-10.7-24-24-24l-144 0z"/></svg> [EML](https://en.wikipedia.org/wiki/Email#Filename_extensions) <img alt="EPUB logo" src="https://upload.wikimedia.org/wikipedia/commons/9/91/Epub_logo.svg" style="height:20px;max-width:20px;"> [EPUB](https://marph91.github.io/jimmy/formats/default/)
`F` <img alt="Fountain logo" src="https://fountain.io/wp-content/uploads/2023/05/fountain-sign-164-150x150.png" style="height:20px;max-width:20px;"> [Fountain](https://marph91.github.io/jimmy/formats/default/)
`H` <img alt="HTML logo" src="https://upload.wikimedia.org/wikipedia/commons/6/61/HTML5_logo_and_wordmark.svg" style="height:20px;max-width:20px;"> [HTML](https://marph91.github.io/jimmy/formats/default/)
`J` <img alt="Jupyter Notebook logo" src="https://upload.wikimedia.org/wikipedia/commons/3/38/Jupyter_logo.svg" style="height:20px;max-width:20px;"> [Jupyter Notebook](https://marph91.github.io/jimmy/formats/default/)
`M` <img alt="Markdown logo" src="https://upload.wikimedia.org/wikipedia/commons/f/f4/Markdown-mark-4th.svg" style="height:20px;max-width:20px;"> [Markdown](https://marph91.github.io/jimmy/formats/default/) <img alt="MediaWiki logo" src="https://www.mediawiki.org/static/images/icons/mediawikiwiki.svg" style="height:20px;max-width:20px;"> [MediaWiki](https://marph91.github.io/jimmy/formats/default/)
`O` <img alt="ODT logo" src="https://upload.wikimedia.org/wikipedia/commons/0/02/LibreOffice_6.1_Writer_Icon.svg" style="height:20px;max-width:20px;"> [ODT](https://marph91.github.io/jimmy/formats/default/) <img alt="OPML logo" src="https://upload.wikimedia.org/wikipedia/commons/2/2c/Opml-icon.svg" style="height:20px;max-width:20px;"> [OPML](https://marph91.github.io/jimmy/formats/default/)
`R` <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 384 512" style="height:20px;max-width:20px;" fill="gray" opacity="0.5"><!--!Font Awesome Free 6.7.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2025 Fonticons, Inc.--><path d="M64 464c-8.8 0-16-7.2-16-16L48 64c0-8.8 7.2-16 16-16l160 0 0 80c0 17.7 14.3 32 32 32l80 0 0 288c0 8.8-7.2 16-16 16L64 464zM64 0C28.7 0 0 28.7 0 64L0 448c0 35.3 28.7 64 64 64l256 0c35.3 0 64-28.7 64-64l0-293.5c0-17-6.7-33.3-18.7-45.3L274.7 18.7C262.7 6.7 246.5 0 229.5 0L64 0zm56 256c-13.3 0-24 10.7-24 24s10.7 24 24 24l144 0c13.3 0 24-10.7 24-24s-10.7-24-24-24l-144 0zm0 96c-13.3 0-24 10.7-24 24s10.7 24 24 24l144 0c13.3 0 24-10.7 24-24s-10.7-24-24-24l-144 0z"/></svg> [reStructuredText](https://marph91.github.io/jimmy/formats/default/) <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 384 512" style="height:20px;max-width:20px;" fill="gray" opacity="0.5"><!--!Font Awesome Free 6.7.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2025 Fonticons, Inc.--><path d="M64 464c-8.8 0-16-7.2-16-16L48 64c0-8.8 7.2-16 16-16l160 0 0 80c0 17.7 14.3 32 32 32l80 0 0 288c0 8.8-7.2 16-16 16L64 464zM64 0C28.7 0 0 28.7 0 64L0 448c0 35.3 28.7 64 64 64l256 0c35.3 0 64-28.7 64-64l0-293.5c0-17-6.7-33.3-18.7-45.3L274.7 18.7C262.7 6.7 246.5 0 229.5 0L64 0zm56 256c-13.3 0-24 10.7-24 24s10.7 24 24 24l144 0c13.3 0 24-10.7 24-24s-10.7-24-24-24l-144 0zm0 96c-13.3 0-24 10.7-24 24s10.7 24 24 24l144 0c13.3 0 24-10.7 24-24s-10.7-24-24-24l-144 0z"/></svg> [RTF](https://marph91.github.io/jimmy/formats/default/)
`T` <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 384 512" style="height:20px;max-width:20px;" fill="gray" opacity="0.5"><!--!Font Awesome Free 6.7.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2025 Fonticons, Inc.--><path d="M64 464c-8.8 0-16-7.2-16-16L48 64c0-8.8 7.2-16 16-16l160 0 0 80c0 17.7 14.3 32 32 32l80 0 0 288c0 8.8-7.2 16-16 16L64 464zM64 0C28.7 0 0 28.7 0 64L0 448c0 35.3 28.7 64 64 64l256 0c35.3 0 64-28.7 64-64l0-293.5c0-17-6.7-33.3-18.7-45.3L274.7 18.7C262.7 6.7 246.5 0 229.5 0L64 0zm56 256c-13.3 0-24 10.7-24 24s10.7 24 24 24l144 0c13.3 0 24-10.7 24-24s-10.7-24-24-24l-144 0zm0 96c-13.3 0-24 10.7-24 24s10.7 24 24 24l144 0c13.3 0 24-10.7 24-24s-10.7-24-24-24l-144 0z"/></svg> [txt2tags](https://marph91.github.io/jimmy/formats/default/)

## General Usage

```mermaid
flowchart LR
    A[App 1] -->|Backup| M
    B[App 2] -->|Export| M
    C[...] --> M
    D[Filesystem] --> M
    M(ZIP archive/JSON/Folder) --> N
    N{Jimmy} --> O(Markdown + Frontmatter)
    O -->|Import| P[Joplin]
    O -->|Import| Q[Obsidian]
    O --> R[...]
    O --> S[Editor, e. g. VSCode]
```

1. Export/backup notes from your note application
2. Run `jimmy`, which converts your notes to Markdown
3. Import the result to Joplin/Obsidian or use any editor to view the notes

After conversion, the notes should be available in a folder named like `YYYY-MM-DD HH:MM:SS - Import`. Make sure your data is converted properly :exclamation:

What is converted (in most cases)?

- Note content
- Tags / Labels
- Images / Resources / Attachments
- External links and internal note links

## Step-by-step Instructions

| Step | Linux / macOS Example | Windows Example |
| --- | --- | --- |
| Export your notes to your download folder | `/home/user/Downloads/Export.zip` | `C:\Users\user\Downloads\Export.zip` |
| Download Jimmy to your download folder [1] | `/home/user/Downloads/jimmy-cli-linux` | `C:\Users\user\Downloads\jimmy-cli-windows.exe` |
| Open a terminal | [Linux](https://www.wikihow.com/Open-a-Terminal-Window-in-Ubuntu) / [macOS](https://www.wikihow.com/Open-a-Terminal-Window-in-Mac) instructions | [Windows instructions](https://www.wikihow.com/Open-Terminal-in-Windows) |
| Change to the download folder | `cd /home/user/Downloads/` | `cd C:\Users\user\Downloads\` |
| Make Jimmy executable | `chmod +x jimmy-cli-linux` | \-  |
| Do the conversion [2] [3] [4] | `./jimmy-cli-linux Export.zip --format notion` | `jimmy-cli-windows.exe Export.zip --format notion` |
| Check the output folder | `/home/user/Downloads/20250226T200101Z - Jimmy Import from notion` | `C:\Users\user\Downloads\20250226T200101Z - Jimmy Import from notion` |

[1] On Windows: If Jimmy is flagged as virus, please [report the false positive to your antivirus vendor](https://github.com/pyinstaller/pyinstaller/blob/c7f12ccfaa2e116c3b7cfb58dadfc1e6b8c6882d/.github/ISSUE_TEMPLATE/antivirus.md#reporting-false-positives-to-av-vendors). As workaround, you can try an older version of Jimmy.

[2] On macOS: If there is the error message `zsh: bad CPU type in executable`, please use [this executable](https://github.com/marph91/jimmy/releases/latest/download/jimmy-cli-darwin-x86_64). It is supported by Intel chips.

[3] On macOS: If there is the error message `"jimmy-cli-darwin-arm64" cannot be opened because the developer cannot be verified`, please authorize Jimmy at `System Settings → Privacy & Security → Security → Open Anyway`. See also the [Apple support guide](https://support.apple.com/en-gb/guide/mac-help/mchlc5fb7f9c/mac).

[4] On Linux: If there is the error message ``version `GLIBC_2.35' not found``, you can either try update your OS or use an older Jimmy build. The glibc version is usually upwards compatible:

| Jimmy Version | Glibc Version |
| --- | --- |
| From [v1.0.0](https://github.com/marph91/jimmy/releases/tag/v0.1.0) | 2.35 |
| [v0.0.56](https://github.com/marph91/jimmy/releases/tag/v0.0.56) | 2.31 |

## Similar Projects

- [Notesnook Importer](https://github.com/streetwriters/notesnook-importer)
- [Obsidian-Importer](https://github.com/obsidianmd/obsidian-importer)
- [YANOM-Note-O-Matic (fork)](https://github.com/stereohorse/YANOM-Note-O-Matic)
- [MarkItDown](https://github.com/microsoft/markitdown)
