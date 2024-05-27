#!/bin/bash

# for manual testing

set -e

CACHE=".cache"  # created at a testsuite run

EXECUTABLE="${1:-python src/jimmy_cli.py}"
echo "Running with $EXECUTABLE"

$EXECUTABLE "$CACHE"
$EXECUTABLE "$CACHE/arbitrary_folder" "$CACHE"
$EXECUTABLE "$CACHE/clipto/clipto_backup_240401_105154.json" --format clipto
$EXECUTABLE "$CACHE/dynalist/dynalist-backup-2024-04-12.zip" --format dynalist
$EXECUTABLE "$CACHE/google_keep/takeout-20240401T160516Z-001.zip" --format google_keep
$EXECUTABLE "$CACHE/google_keep/takeout-20240401T160556Z-001.tgz" --format google_keep
$EXECUTABLE "$CACHE/joplin/29_04_2024.jex" --format joplin
$EXECUTABLE "$CACHE/nimbus_note/Food" --format nimbus_note
$EXECUTABLE "$CACHE/notion/72a2f31c-3a46-4b44-826d-ae046e693551_Export-d609fb9f-43a4-475d-ba88-1db3e9e6bcd2.zip" --format notion
$EXECUTABLE "$CACHE/obsidian/obsidian_vault" --format obsidian
$EXECUTABLE "$CACHE/simplenote/notes.zip" --format simplenote
$EXECUTABLE "$CACHE/standard_notes/Standard Notes Backup - Sun Apr 28 2024 12_56_55 GMT+0200.zip" --format standard_notes
$EXECUTABLE "$CACHE/synology_note_station/notestation-test-books.nsx" --format synology_note_station
# $EXECUTABLE "$CACHE/tiddlywiki/tiddlers.json" --format tiddlywiki
$EXECUTABLE "$CACHE/todo_txt/examples_from_readme.txt" --format todo_txt
$EXECUTABLE "$CACHE/todoist/Privates.csv" --format todoist
$EXECUTABLE "$CACHE/toodledo/toodledo_completed_240427.csv" --format toodledo
$EXECUTABLE "$CACHE/toodledo/toodledo_current_240427.csv" --format toodledo
$EXECUTABLE "$CACHE/toodledo/toodledo_notebook_240427.csv" --format toodledo
$EXECUTABLE "$CACHE/zim_md"
$EXECUTABLE "$CACHE/zoho_notebook/Notebook_14Apr2024_1300_html.zip" --format zoho_notebook
