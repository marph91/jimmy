---
source_app: Notability
---

# Convert from Notability to Markdown

❎ Currently not supported by Jimmy.

## General Information

- [Website](https://notability.com/)
- Typical extensions: `.note` files

## Known Limitations

Unfortunately, it's not possible to share notes in an open format without a premium account. You can either export to an image and extract the text via another OCR tool or export as `.note` (see below).

## Notes on the proprietary .note format

It would be desirable to convert Notability's `.note` files directly, as they should contain all information. The `.note` files are zip archives with content:

```
├── Assets
├── HandwritingIndex
├── Images
│   ├── Image 1.jpg
│   └── Image .jpg
├── metadata.plist
├── PDFs
├── Recordings
│   ├── library.plist
│   └── Recording 1.m4a
├── Session.plist
└── thumb12x.png
```

The `.plist` files can be parsed with Python's built-in [`plistlib`](https://docs.python.org/3/library/plistlib.html). But they contain many unknown UIDs and binary strings. It was not possible to reverse engineer the complete files in a reasonable amount of time, though. If you have any information about the layout, please share.
