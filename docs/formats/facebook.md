---
description: Convert from Facebook to Markdown.
---

# Convert from Facebook to Markdown

## General Information

- [Website](https://www.facebook.com/)
- Typical extension: `.zip`

## Instructions

1. Export as described [at the website](https://www.facebook.com/help/212802592074644/)
    1. Choose JSON
    2. The export may take some time. For a 450 MB file it took two days.
2. [Install Jimmy](../index.md#installation)
3. Convert to Markdown. Example: `jimmy-cli-linux facebook-xyz-07.07.2024-m9lv24pS.zip --format facebook`
4. [Import to your app](../import_instructions.md)

## Import Structure

- Posts and messages are stored in separate notebooks.
- Each post is converted to a separate note, starting with the creation date (`YYYY-MM-DD`).
- Each conversation is a note. Messages are concatenated inside the note and separated by the day. Conversations may be split to prevent too big notes.
- Referenced resources (audio, gif, photos, videos and other files) are converted.

## Known Limitations

The import was tested with many messages (450 MB, >50000 messages) and only a few posts (~20 posts). The import may be not robust enough yet.

- Shared posts are not converted.
- Profile images, stories and shorts are not converted.
- Group chats are not converted, since Facebook creates a new file every time a person joins or leaves. It's not possible to merge them by ID.
