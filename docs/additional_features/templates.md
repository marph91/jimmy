---
description: This page describes how to use templates in Jimmy.
---

Templates can be used to customize notes. You can specify a template by `--template my_template.txt`.

!!! warning
    This feature is experimental and may break at any time.

## Examples

### Add the note title as heading 1 on top of the note

[Template](https://github.com/marph91/jimmy-test-data/blob/2a58f94f635ff4fcf940ab51551e7436d7d5c6cd/test_data/template/title_heading.txt):

```
# {title}

{body}
```

### Define custom front matter

[Template](https://github.com/marph91/jimmy-test-data/blob/2a58f94f635ff4fcf940ab51551e7436d7d5c6cd/test_data/template/custom_frontmatter.txt):

```
---
title: {title}
author: {author}
latitude: {latitude:.3f}
longitude: {longitude:.0f}
altitude: {altitude}
created: {created:%Y-%m-%dT%H:%M:%SZ}
updated: {updated:%Y-%m-%dT%H:%M:%SZ}
tags: {tags}
resources: {resources}
note_links: {note_links}
---

{body}
```

## Define an overview table

[Template](https://github.com/marph91/jimmy-test-data/blob/2a58f94f635ff4fcf940ab51551e7436d7d5c6cd/test_data/template/table.txt):

```
|         |                              |
| ------- | ---------------------------- |
| From    | {author}                     |
| Title   | {title}                      |
| Date    | {created:%Y-%m-%dT%H:%M:%SZ} |

---

{body}
```
