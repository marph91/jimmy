#!/bin/bash

# for manual testing

set -e

CACHE=".cache"  # created at a testsuite run

EXECUTABLE="${1:-python src/jimmy.py}"
echo "Running with $EXECUTABLE"

$EXECUTABLE "$CACHE"
$EXECUTABLE "$CACHE/arbitrary_folder" "$CACHE"
$EXECUTABLE "$CACHE/clipto/clipto_backup_240401_105154.json" --app clipto
$EXECUTABLE "$CACHE/dynalist/dynalist-backup-2024-04-12.zip" --app dynalist
$EXECUTABLE "$CACHE/google_keep/takeout-20240401T160516Z-001.zip" --app google_keep
$EXECUTABLE "$CACHE/google_keep/takeout-20240401T160556Z-001.tgz" --app google_keep
$EXECUTABLE "$CACHE/joplin/29_04_2024.jex" --app joplin
$EXECUTABLE "$CACHE/nimbus_note/Food" --app nimbus_note
$EXECUTABLE "$CACHE/notion/72a2f31c-3a46-4b44-826d-ae046e693551_Export-d609fb9f-43a4-475d-ba88-1db3e9e6bcd2.zip" --app notion
$EXECUTABLE "$CACHE/obsidian/obsidian_vault" --app obsidian
$EXECUTABLE "$CACHE/simplenote/notes.zip" --app simplenote
$EXECUTABLE "$CACHE/standard_notes/Standard Notes Backup - Sun Apr 28 2024 12_56_55 GMT+0200.zip" --app standard_notes
$EXECUTABLE "$CACHE/synology_note_station/notestation-test-books.nsx" --app synology_note_station
# $EXECUTABLE "$CACHE/tiddlywiki/tiddlers.json" --app tiddlywiki
$EXECUTABLE "$CACHE/todo_txt/examples_from_readme.txt" --app todo_txt
$EXECUTABLE "$CACHE/todoist/Privates.csv" --app todoist
$EXECUTABLE "$CACHE/toodledo/toodledo_completed_240427.csv" --app toodledo
$EXECUTABLE "$CACHE/toodledo/toodledo_current_240427.csv" --app toodledo
$EXECUTABLE "$CACHE/toodledo/toodledo_notebook_240427.csv" --app toodledo
$EXECUTABLE "$CACHE/zim_md"
$EXECUTABLE "$CACHE/zoho_notebook/Notebook_14Apr2024_1300_html.zip" --app zoho_notebook
