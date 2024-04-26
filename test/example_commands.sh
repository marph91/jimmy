#!/bin/bash

# for manual testing

set -e

CACHE=".cache"  # created at a testsuite run

python src/joplin_custom_importer.py "$CACHE"
python src/joplin_custom_importer.py "$CACHE/arbitrary_folder" "$CACHE"

# This is a local directory, because it contains user data.
if [ -d "temp" ]; then
    python src/joplin_custom_importer.py "$CACHE/nimbus_export_user/Food\ Original\ export\ from\ Nimbus/" --app nimbus_note
    python src/joplin_custom_importer.py "$CACHE/notion/72a2f31c-3a46-4b44-826d-ae046e693551_Export-d609fb9f-43a4-475d-ba88-1db3e9e6bcd2.zip" --app notion
    # python src/joplin_custom_importer.py "$CACHE/tiddlywiki/tiddlers.json" --app tiddlywiki
fi

python src/joplin_custom_importer.py "$CACHE/clipto/clipto_backup_240401_105154.json" --app clipto
python src/joplin_custom_importer.py "$CACHE/dynalist/dynalist-backup-2024-04-12.zip" --app dynalist
python src/joplin_custom_importer.py "$CACHE/google_keep/takeout-20240401T160516Z-001.zip" --app google_keep
python src/joplin_custom_importer.py "$CACHE/google_keep/takeout-20240401T160556Z-001.tgz" --app google_keep
python src/joplin_custom_importer.py "$CACHE/obsidian/obsidian_vault" --app obsidian
python src/joplin_custom_importer.py "$CACHE/simplenote/notes.zip" --app simplenote
python src/joplin_custom_importer.py "$CACHE/synology_note_station/notestation-test-books.nsx" --app synology_note_station
python src/joplin_custom_importer.py "$CACHE/todo_txt/examples_from_readme.txt" --app todo_txt
python src/joplin_custom_importer.py "$CACHE/todoist/Privates.csv" --app todoist
python src/joplin_custom_importer.py "$CACHE/zoho_notebook/Notebook_14Apr2024_1300_html.zip" --app zoho_notebook
