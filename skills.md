# Jimmy - Note Format Converter

## Overview

Jimmy is a comprehensive open-source tool designed to convert notes from various applications and formats into Markdown. It serves as a universal note migration and conversion utility that supports over 50 different note-taking apps and document formats.

## Key Features

- **Universal Format Support**: Converts from 50+ note-taking applications and document formats
- **Markdown Output**: Produces clean, future-proof Markdown with frontmatter
- **Cross-Platform**: Works on Linux, Windows, and macOS
- **Standalone Binary**: No Docker, Python, or Node.js installation required
- **Dual Interface**: Both Command Line Interface (CLI) and Terminal User Interface (TUI)
- **Offline Operation**: Completely offline, no internet connection required
- **Comprehensive Conversion**: Preserves tags, resources, attachments, and note links

## Supported Applications

Jimmy supports importing from popular note-taking applications including:
- **Major Platforms**: Notion, Evernote, OneNote, Obsidian, Joplin
- **Mobile Apps**: Google Keep, Apple Notes (via various exports), Samsung Notes
- **Desktop Apps**: Bear, CherryTree, RedNotebook, QOwnNotes
- **Cloud Services**: Dropbox Paper, Facebook Notes, WordPress
- **Specialized**: Anki cards, Zettelkasten, Roam Research, Dynalist

## Supported Document Formats

In addition to note applications, Jimmy can convert:
- **Office Documents**: DOCX, ODT, PDF, EPUB
- **Markup Languages**: Markdown, HTML, AsciiDoc, reStructuredText
- **Structured Data**: CSV, OPML, Jupyter Notebooks
- **Email**: EML files

## Use Cases

1. **Migration**: Move notes between different note-taking applications
2. **Archive**: Convert notes to a future-proof, human-readable format
3. **LLM Preparation**: Format notes for processing with Large Language Models
4. **Batch Conversion**: Convert entire folders of documents recursively

## Technical Architecture

- **Intermediate Format**: Uses a standardized intermediate representation to handle different input formats
- **Plugin System**: Modular format converters in `jimmy/formats/` directory
- **Pandoc Integration**: Leverages Pandoc for document format conversion
- **Rich Output**: Provides detailed logging and progress information

## Development

- **Language**: Python 3.14+
- **Build System**: Hatchling with pyinstaller for binary distribution
- **Testing**: Comprehensive test suite with pytest
- **Linting**: Uses ruff, mypy, and pylint for code quality
- **Documentation**: MkDocs-based documentation site

## Project Structure

```
jimmy/
├── formats/          # Format-specific converters
│   ├── notion.py    # Notion importer
│   ├── evernote.py  # Evernote importer
│   └── ...          # 50+ format converters
├── intermediate_format.py  # Data structure definitions
├── converter.py      # Core conversion logic
├── writer.py        # Markdown output generation
├── filters.py       # Post-processing filters
└── jimmy_cli.py     # Command line interface
```

## Contributing

The project welcomes contributions in various forms:
- **Format Support**: Adding support for new note applications
- **Documentation**: Improving existing documentation
- **Testing**: Providing test files and bug reports
- **Community**: Sharing feedback and use cases

## Installation

Jimmy is distributed as precompiled binaries for all major platforms, making it easy to use without any Python dependencies.

## License

GPL-3.0 - Open source with strong copyleft protections.

This tool is essential for anyone looking to migrate notes between applications, archive digital content, or prepare notes for AI processing while maintaining data integrity and preserving metadata.