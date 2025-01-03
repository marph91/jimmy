# jimmy

Free your notes by converting them to Markdown.

:floppy_disk: Download: [**Linux**](https://github.com/marph91/jimmy/releases/latest/download/jimmy-cli-linux) | [**Windows**](https://github.com/marph91/jimmy/releases/latest/download/jimmy-cli-windows.exe) | [**MacOS**](https://github.com/marph91/jimmy/releases/latest/download/jimmy-cli-darwin-arm64)  [![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/marph91/jimmy/total)](https://github.com/marph91/jimmy/releases/latest)

:blue_book: For detailed information, take a look at the [Documentation](https://marph91.github.io/jimmy/).

:star: If this app is useful for you, feel free to star it on [github](https://github.com/marph91/jimmy).

[![build](https://github.com/marph91/jimmy/actions/workflows/build.yml/badge.svg)](https://github.com/marph91/jimmy/actions/workflows/build.yml)
[![lint](https://github.com/marph91/jimmy/actions/workflows/lint.yml/badge.svg)](https://github.com/marph91/jimmy/actions/workflows/lint.yml)
[![tests](https://github.com/marph91/jimmy/actions/workflows/tests.yml/badge.svg)](https://github.com/marph91/jimmy/actions/workflows/tests.yml)

## Features

- ✅ Several supported input formats
- ✅ Markdown + Frontmatter output
    - Compatible with any text editor
    - Can be imported to Joplin/Obsidian/...
    - Preserves resources, tags and note links when possible
- ✅ Offline
- ✅ Open Source
- ✅ Cross-platform
- ✅ Standalone (no Docker, Python or NodeJS installation required)
- ❎ No AI

## Supported Apps

Export data from your app and convert it to Markdown. For details, click on the links.

||||||
| :--- | :---: | :---: | :---: | :---: |
| **A** | <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/3/3d/Anki-icon.svg/240px-Anki-icon.svg.png" style="height:100px;max-width:100px;"><br>[Anki](https://marph91.github.io/jimmy/formats/anki/) | <img src="https://raw.githubusercontent.com/anyproto/anytype-ts/refs/heads/main/src/img/logo/symbol.svg" style="height:100px;max-width:100px;"><br>[Anytype](https://marph91.github.io/jimmy/formats/anytype/) |
| **B** | <img src="https://bear.app/images/logo.png" style="height:100px;max-width:100px;"><br>[Bear](https://marph91.github.io/jimmy/formats/bear/) |
| **C** | <img src="https://raw.githubusercontent.com/CacherApp/cacher-cli/e241f06867dba740131db5314ef7fe279135baf6/images/cacher-icon.png" style="height:100px;max-width:100px;"><br>[Cacher](https://marph91.github.io/jimmy/formats/cacher/) | <img src="https://raw.githubusercontent.com/giuspen/cherrytree/c822b16681b002b8882645d8d1e8f109514ddb58/icons/cherrytree.svg" style="height:100px;max-width:100px;"><br>[CherryTree](https://marph91.github.io/jimmy/formats/cherrytree/) | <img src="https://avatars.githubusercontent.com/u/53916365?s=200&v=4" style="height:100px;max-width:100px;"><br>[Clipto](https://marph91.github.io/jimmy/formats/clipto/) | <img src="https://www.colornote.com/wp-content/uploads/2016/05/cropped-favicon.png" style="height:100px;max-width:100px;"><br>[ColorNote](https://marph91.github.io/jimmy/formats/colornote/) |
| **D** | <img src="https://iconape.com/wp-content/files/rb/342127/png/day-one-logo.png" style="height:100px;max-width:100px;"><br>[Day&nbsp;One](https://marph91.github.io/jimmy/formats/day_one/) | <img src="https://images.saasworthy.com/dynalist_5288_logo_1576239391_xhkcg.jpg" style="height:100px;max-width:100px;"><br>[Dynalist](https://marph91.github.io/jimmy/formats/dynalist/) |
| **E** | <img src="https://avatars.githubusercontent.com/u/1120885" style="height:100px;max-width:100px;"><br>[Evernote](https://marph91.github.io/jimmy/formats/evernote/) |
| **F** | <img src="https://upload.wikimedia.org/wikipedia/commons/b/b8/2021_Facebook_icon.svg" style="height:100px;max-width:100px;"><br>[Facebook](https://marph91.github.io/jimmy/formats/facebook/) | <img src="https://wavebox.pro/store2/store/0b46bf0a-107c-4fa2-a657-3df7412e3d3d.png" style="height:100px;max-width:100px;"><br>[FuseBase, Nimbus&nbsp;Note](https://marph91.github.io/jimmy/formats/fusebase/) |
| **G** | <img src="https://www.gstatic.com/images/branding/product/1x/docs_2020q4_96dp.png" style="height:100px;max-width:100px;"><br>[Google&nbsp;Docs](https://marph91.github.io/jimmy/formats/google_docs/) | <img src="https://www.gstatic.com/images/branding/product/1x/keep_2020q4_96dp.png" style="height:100px;max-width:100px;"><br>[Google&nbsp;Keep](https://marph91.github.io/jimmy/formats/google_keep/) |
| **J** | <img src="https://github.com/laurent22/joplin/blob/dev/Assets/LinuxIcons/128x128.png?raw=true" style="height:100px;max-width:100px;"><br>[Joplin](https://marph91.github.io/jimmy/formats/joplin/) | <img src="https://raw.githubusercontent.com/jrnl-org/jrnl/85a98afcd91ed873c0eceba9893c3ec424f201b8/docs_theme/img/logo.svg" style="height:100px;max-width:100px;"><br>[jrnl](https://marph91.github.io/jimmy/formats/jrnl/) |
| **N** | <img src="https://upload.wikimedia.org/wikipedia/commons/4/45/Notion_app_logo.png" style="height:100px;max-width:100px;"><br>[Notion](https://marph91.github.io/jimmy/formats/notion/) |
| **O** | <img src="https://upload.wikimedia.org/wikipedia/commons/1/10/2023_Obsidian_logo.svg" style="height:100px;max-width:100px;"><br>[Obsidian](https://marph91.github.io/jimmy/formats/obsidian/) |
| **Q** | <img src="https://raw.githubusercontent.com/pbek/QOwnNotes/d89a597a28eeb16f57692ac121933b478f44bf07/src/images/icons/256x256/apps/QOwnNotes.png" style="height:100px;max-width:100px;"><br>[QOwnNotes](https://marph91.github.io/jimmy/formats/qownnotes/) |
| **R** | <img src="https://raw.githubusercontent.com/jendrikseipp/rednotebook/b2cefe5f321b21ab7ad855059f3c0496eb0830d2/rednotebook/images/rednotebook-icon/rn-256.png" style="height:100px;max-width:100px;"><br>[RedNotebook](https://marph91.github.io/jimmy/formats/rednotebook/) |
| **S** | <img src="https://raw.githubusercontent.com/Automattic/simplenote-electron/4a140a96545763c849b26a81a2e27ff67eaa68f0/lib/icons/app-icon/icon_256x256.png" style="height:100px;max-width:100px;"><br>[Simplenote](https://marph91.github.io/jimmy/formats/simplenote/) | <img src="https://avatars.githubusercontent.com/u/24537496?s=100" style="height:100px;max-width:100px;"><br>[Standard&nbsp;Notes](https://marph91.github.io/jimmy/formats/standard_notes/) | <img src="https://www.synology.com/img/dsm/note_station/notestation_72.png" style="height:100px;max-width:100px;"><br>[Synology Note&nbsp;Station](https://marph91.github.io/jimmy/formats/synology_note_station/) |
| **T** | [Textbundle, Textpack](https://marph91.github.io/jimmy/formats/textbundle/) | <img src="https://talk.tiddlywiki.org/uploads/default/original/1X/5d4e8afa05b64280281f851dfc982796b5f7fcd1.svg" style="height:100px;max-width:100px;"><br>[Tiddlywiki](https://marph91.github.io/jimmy/formats/tiddlywiki/) | <img src="https://dl.flathub.org/media/org/gnome/Gnote/4f2ede31f33a5f935bec4206a6035410/icons/128x128/org.gnome.Gnote.png" style="height:100px;max-width:100px;"><br>[Tomboy-ng, Gnote](https://marph91.github.io/jimmy/formats/tomboy_ng/) | <img src="https://turtlapp.com/images/logo.svg" style="height:100px;max-width:100px;"><br>[Turtl](https://marph91.github.io/jimmy/formats/turtl/) |
| **W** | <img src="https://s.w.org/style/images/about/WordPress-logotype-wmark.png" style="height:100px;max-width:100px;"><br>[Wordpress](https://marph91.github.io/jimmy/formats/wordpress/) |
| **Z** | <img src="https://raw.githubusercontent.com/Zettelkasten-Team/Zettelkasten/refs/heads/main/src/main/resources/de/danielluedecke/zettelkasten/resources/icons/zkn3-256x256.png" style="height:100px;max-width:100px;"><br>[Zettelkasten](https://marph91.github.io/jimmy/formats/zettelkasten/) | <img src="https://zim-wiki.org/images/globe.png" style="height:100px;max-width:100px;"><br>[Zim](https://marph91.github.io/jimmy/formats/zim/) | <img src="https://zohowebstatic.com/sites/default/files/ogimage/notebook-logo.png" style="height:100px;max-width:100px;"><br>[Zoho&nbsp;Notebook](https://marph91.github.io/jimmy/formats/zoho_notebook/) |

## Supported Formats

Import a single file or a folder (recursively). Files of these formats will be converted to Markdown. The formats can be mixed. For example you can import a folder with two Asciidoc files and one docx file. The conversion result will be a folder with three Markdown files and the corresponding attachments.

||||
| :--- | :---: | :---: |
| **A** | <img src="https://avatars.githubusercontent.com/u/3137042?s=100&v=4" style="height:100px;max-width:100px;"><br>[Asciidoc](https://marph91.github.io/jimmy/formats/default/) |
| **C** | <img src="https://upload.wikimedia.org/wikipedia/commons/3/34/Microsoft_Office_Excel_%282019%E2%80%93present%29.svg" style="height:100px;max-width:100px;"><br>[CSV](https://marph91.github.io/jimmy/formats/default/) |
| **D** | [DocBook](https://marph91.github.io/jimmy/formats/default/) | <img src="https://upload.wikimedia.org/wikipedia/commons/f/fd/Microsoft_Office_Word_%282019%E2%80%93present%29.svg" style="height:100px;max-width:100px;"><br>[docx](https://marph91.github.io/jimmy/formats/default/) |
| **E** | [eml](https://en.wikipedia.org/wiki/Email#Filename_extensions) | <img src="https://upload.wikimedia.org/wikipedia/commons/9/91/Epub_logo.svg" style="height:100px;max-width:100px;"><br>[EPUB](https://marph91.github.io/jimmy/formats/default/) |
| **F** | <img src="https://fountain.io/wp-content/uploads/2023/05/fountain-sign-164-150x150.png" style="height:100px;max-width:100px;"><br>[Fountain](https://marph91.github.io/jimmy/formats/default/) |
| **H** | <img src="https://upload.wikimedia.org/wikipedia/commons/6/61/HTML5_logo_and_wordmark.svg" style="height:100px;max-width:100px;"><br>[HTML](https://marph91.github.io/jimmy/formats/default/) |
| **J** | <img src="https://upload.wikimedia.org/wikipedia/commons/3/38/Jupyter_logo.svg" style="height:100px;max-width:100px;"><br>[Jupyter Notebook](https://marph91.github.io/jimmy/formats/default/) |
| **M** | <img src="https://upload.wikimedia.org/wikipedia/commons/f/f4/Markdown-mark-4th.svg" style="height:100px;max-width:100px;"><br>[Markdown](https://marph91.github.io/jimmy/formats/default/) | <img src="https://www.mediawiki.org/static/images/icons/mediawikiwiki.svg" style="height:100px;max-width:100px;"><br>[MediaWiki](https://marph91.github.io/jimmy/formats/default/) |
| **O** | <img src="https://upload.wikimedia.org/wikipedia/commons/0/02/LibreOffice_6.1_Writer_Icon.svg" style="height:100px;max-width:100px;"><br>[ODT](https://marph91.github.io/jimmy/formats/default/) | <img src="https://upload.wikimedia.org/wikipedia/commons/2/2c/Opml-icon.svg" style="height:100px;max-width:100px;"><br>[OPML](https://marph91.github.io/jimmy/formats/default/) |
| **R** | [reStructuredText](https://marph91.github.io/jimmy/formats/default/) | [RTF](https://marph91.github.io/jimmy/formats/default/) |
| **T** | [txt2tags](https://marph91.github.io/jimmy/formats/default/) |

## General Usage

```mermaid
flowchart LR
    A[App 1] -->|Backup| M
    B[App 2] -->|Export| M
    C[...] --> M
    D[Filesystem] --> M
    M(ZIP archive/JSON/Folder) --> N
    N{jimmy} --> O(Markdown + Frontmatter)
    O -->|Import| P[Joplin]
    O -->|Import| Q[Obsidian]
    O --> R[...]
    O --> S[Editor, e. g. VSCode]
```

1. Export/backup notes from your note application
2. Run `jimmy`, which converts your notes to Markdown
3. Import the result to Joplin/Obsidian or use any editor to view the notes

For detailed instructions, see the page of the [specific format](https://marph91.github.io/jimmy/formats/default/).

## Quickstart

1. Download jimmy here: [**Linux**](https://github.com/marph91/jimmy/releases/latest/download/jimmy-cli-linux) | [**Windows**](https://github.com/marph91/jimmy/releases/latest/download/jimmy-cli-windows.exe) | [**MacOS**](https://github.com/marph91/jimmy/releases/latest/download/jimmy-cli-darwin-arm64)
2. Examples for the Linux CLI app:

```bash
# import a single file supported by pandoc
jimmy-cli-linux libre_office_document.odt

# import all files in a folder
jimmy-cli-linux path/to/folder

# import a Google Keep export
jimmy-cli-linux takeout-20240401T160516Z-001.zip --format google_keep
```

After conversion, the notes should be available in a folder named like `YYYY-MM-DD HH:MM:SS - Import`. Make sure your data is converted properly :exclamation:

What is converted (in most cases)?

- Note content
- Tags / Labels
- Images / Resources / Attachments
- External links and internal note links

If something is not working, please check the issues first. If you can't find anything, feel free to create a new issue. It might be just not implemented yet or a regression. On the other side, the exported data can be sparse. In that case it's not possible to transfer the data with jimmy.

## Demo

This is an example of a successful conversion:

```bash
$ jimmy-cli-linux .cache/google_keep/takeout-20240401T160516Z-001.zip --format google_keep --frontmatter joplin
[09/19/24 15:15:34] INFO     Importing notes from ".cache/google_keep/takeout-20240401T160516Z-001.zip"
                    INFO     Start parsing
                    INFO     Finished parsing: 1 notebooks, 3 notes, 1 resources, 3 tags
                    INFO     Start filtering
                    INFO     Finished filtering: 1 notebooks, 3 notes, 1 resources, 3 tags
                    INFO     Start writing to file system
                    INFO     Converted notes successfully to Markdown: "20240919T131534Z - Jimmy Import from google_keep". Please verify that everything was converted correctly.
                    INFO     Feel free to open an issue on Github, write a message at the Joplin forum or an email.

Notebooks  100%|████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00]
Notes      100%|████████████████████████████████████████████████████████████████████| 3/3 [00:00<00:00]
Resources  100%|████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00]
Tags       100%|████████████████████████████████████████████████████████████████████| 3/3 [00:00<00:00]
```

## Similar Projects

- [Obsidian-Importer](https://github.com/obsidianmd/obsidian-importer)
- [YANOM-Note-O-Matic (fork)](https://github.com/stereohorse/YANOM-Note-O-Matic)
