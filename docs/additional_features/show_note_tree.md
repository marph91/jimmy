The note tree in the intermediate format can be shown by `--print-tree`.

## Examples

1. Simply show the imported note tree:

```sh
$ jimmy-cli-linux .cache/arbitrary_folder/arbitrary_folder/ --print-tree
[09/17/24 17:39:20] INFO     Importing notes from ".cache/arbitrary_folder/arbitrary_folder"
                    INFO     Start parsing
[09/17/24 17:39:21] INFO     Finished parsing: 3 notebooks, 7 notes, 3 resources, 1 note links
Note Tree
└── 📘 20240917T153920Z - Jimmy Import
    └── 📘 arbitrary_folder
        ├── 📖 sample
        │   ├── 🎴 test.png
        │   └── 🔗 link to second_sample_file
        ├── 📖 plaintext
        ├── 📖 test
        ├── 📖 Big-Fish
        └── 📘 nested_arbitrary_folder
            ├── 📖 LibreOffice Writer
            │   └── 🎴 1000000100000B5F00000449B7E060775BACC2F0.png
            ├── 📖 asciidoc
            │   └── 🎴 test\_image
            └── 📖 second_sample_file
                    INFO     Start filtering
                    INFO     Finished filtering: 3 notebooks, 7 notes, 3 resources, 1 note links
                    INFO     Start writing to file system
                    INFO     Converted notes successfully to Markdown. Please verify that everything was converted correctly.
                    INFO     Feel free to open an issue on Github, write a message at the Joplin forum or an email.

Notebooks  100%|████████████████████████████████████████████████████████████████████████████| 3/3 [00:00<00:00]
Notes      100%|████████████████████████████████████████████████████████████████████████████| 7/7 [00:00<00:00]
Resources  100%|████████████████████████████████████████████████████████████████████████████| 3/3 [00:00<00:00]
Note Links 100%|████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00]
```

2. Verify that the tags are really excluded:

```sh
$ jimmy-cli-linux .cache/obsidian/obsidian_vault --format obsidian --exclude-tags "*" --print-tree
[09/17/24 17:42:14] INFO     Importing notes from ".cache/obsidian/obsidian_vault"
                    INFO     Start parsing
                    INFO     Finished parsing: 2 notebooks, 2 notes, 3 resources, 4 tags, 4 note links
Note Tree
└── 📘 20240917T154214Z - Jimmy Import
    ├── 📖 Sample note
    │   ├── 🎴 markdown image
    │   ├── 🔖 inline-tag-obsidian
    │   ├── 🔖 frontmatter-tag-obsidian
    │   ├── 🔖 another-tag-obsidian
    │   ├── 🔗 alias
    │   └── 🔗 internal link markdown syntax
    └── 📘 folder
        └── 📖 Second sample note
            ├── 🎴 test.png
            ├── 🎴 plaintext.txt
            ├── 🔖 inline-tag-obsidian
            ├── 🔗 Sample note
            └── 🔗 Sample note alias
                    INFO     Start filtering
                    INFO     Finished filtering: 2 notebooks, 2 notes, 3 resources, 4 tags, 4 note links
Note Tree Filtered
└── 📘 20240917T154214Z - Jimmy Import
    ├── 📖 Sample note
    │   ├── 🎴 markdown image
    │   ├── 🔗 alias
    │   └── 🔗 internal link markdown syntax
    └── 📘 folder
        └── 📖 Second sample note
            ├── 🎴 test.png
            ├── 🎴 plaintext.txt
            ├── 🔗 Sample note
            └── 🔗 Sample note alias
                    INFO     Start writing to file system
                    INFO     Converted notes successfully to Markdown. Please verify that everything was converted correctly.
                    INFO     Feel free to open an issue on Github, write a message at the Joplin forum or an email.

Notebooks  100%|████████████████████████████████████████████████████████████████████████████| 2/2 [00:00<00:00]
Notes      100%|████████████████████████████████████████████████████████████████████████████| 2/2 [00:00<00:00]
Resources  100%|████████████████████████████████████████████████████████████████████████████| 3/3 [00:00<00:00]
Note Links 100%|████████████████████████████████████████████████████████████████████████████| 4/4 [00:00<00:00]
```