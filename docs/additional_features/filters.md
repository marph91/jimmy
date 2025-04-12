There are some simple filters to select which data to import. For more complex filtering, a separate plugin or script should be used.

## Available Filters

All filters can be used with wildcard. The filters are case-sensitive.

- Exclude or include specific notes (`--exclude-notes`, `--include-notes`)
- Exclude or include notes with specific tags (`--exclude-notes-with-tags`, `--include-notes-with-tags`)
- Exclude or include the tags themselves (`--exclude-tags`, `--include-tags`)

To check the exact command, visit the help page (`--help`).

## Limitations

Filtering by notebooks is not possible, because nesting can yield some ambiguities.

## Examples

```sh
# show the help
jimmy-cli-linux --help

# import specific nots only
jimmy-cli-linux obsidian_vault/ --format obsidian --include-notes "Sample note" "Second sample note"

# exclude notes with a tag
jimmy-cli-linux obsidian_vault/ --format obsidian --exclude-notes-with-tags "ignore this tag"

# don't import any tags
jimmy-cli-linux obsidian_vault/ --format obsidian --exclude-tags "*"
```
