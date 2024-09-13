#!/bin/bash

# for manual testing

set -e

CACHE=".cache"  # created at a testsuite run

EXECUTABLE="${1:-python src/jimmy_cli.py}"
echo "Running with $EXECUTABLE"

$EXECUTABLE "$CACHE/arbitrary_folder"
$EXECUTABLE "$CACHE/arbitrary_folder" "$CACHE/arbitrary_folder"
$EXECUTABLE "$CACHE/bear/backup.bear2bk" --format bear
$EXECUTABLE "$CACHE/cacher/cacher-export-202406182304.json" --format cacher
$EXECUTABLE "$CACHE/cherrytree/cherry.ctb.ctd" --format cherrytree
$EXECUTABLE "$CACHE/clipto/clipto_backup_240401_105154.json" --format clipto
$EXECUTABLE "$CACHE/day_one/Day.One.zip" --format day_one
$EXECUTABLE "$CACHE/dynalist/dynalist-backup-2024-04-12.zip" --format dynalist
$EXECUTABLE "$CACHE/google_keep/takeout-20240401T160516Z-001.zip" --format google_keep
$EXECUTABLE "$CACHE/google_keep/takeout-20240401T160556Z-001.tgz" --format google_keep
$EXECUTABLE "$CACHE/joplin/29_04_2024.jex" --format joplin
$EXECUTABLE "$CACHE/jrnl/myjournal.json" --format jrnl
$EXECUTABLE "$CACHE/nimbus_note/Food" --format nimbus_note
$EXECUTABLE "$CACHE/notion/72a2f31c-3a46-4b44-826d-ae046e693551_Export-d609fb9f-43a4-475d-ba88-1db3e9e6bcd2.zip" --format notion
$EXECUTABLE "$CACHE/obsidian/obsidian_vault" --format obsidian
$EXECUTABLE "$CACHE/qownnotes/qownnotes_folder" --format qownnotes
$EXECUTABLE "$CACHE/simplenote/notes.zip" --format simplenote
$EXECUTABLE "$CACHE/standard_notes/Standard Notes Backup - Sun Apr 28 2024 12_56_55 GMT+0200.zip" --format standard_notes
$EXECUTABLE "$CACHE/synology_note_station/notestation-test-books.nsx" --format synology_note_station
$EXECUTABLE "$CACHE/textbundle/Textbundle Example v1.textbundle/" --format textbundle
$EXECUTABLE "$CACHE/textbundle/Textbundle Example v2.textbundle/" --format textbundle
$EXECUTABLE "$CACHE/textbundle/example.textpack" --format textbundle
# $EXECUTABLE "$CACHE/tiddlywiki/tiddlyhost.json" --format tiddlywiki
$EXECUTABLE "$CACHE/todo_txt/examples_from_readme.txt" --format todo_txt
$EXECUTABLE "$CACHE/todoist/Privates.csv" --format todoist
$EXECUTABLE "$CACHE/tomboy-ng/tomboy-ng/" --format tomboy_ng
$EXECUTABLE "$CACHE/toodledo/toodledo_completed_240427.csv" --format toodledo
$EXECUTABLE "$CACHE/toodledo/toodledo_current_240427.csv" --format toodledo
$EXECUTABLE "$CACHE/toodledo/toodledo_notebook_240427.csv" --format toodledo
$EXECUTABLE "$CACHE/xit/example.xit" --format xit
$EXECUTABLE "$CACHE/xit/example2.xit" --format xit
$EXECUTABLE "$CACHE/zim_md"
$EXECUTABLE "$CACHE/zoho_notebook/Notebook_14Apr2024_1300_html.zip" --format zoho_notebook
