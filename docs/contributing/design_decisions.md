# Design Decisions

## Why Markdown?

To provide a flexible base for migrating your notes to the app of your choice.

## Why enlighten and not tqdm for progress bars?

enlighten did integrate easier with pythons logging.

## Sort all iterators with arbitrary order

Reproducibility is more important than memory usage and speed.

```python
# good
for item in sorted(file_or_folder.iterdir()):

# bad
for item in file_or_folder.iterdir():
```
