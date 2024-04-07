#!/bin/bash

set -e

python src/joplin_custom_importer.py test_inputs
python src/joplin_custom_importer.py test_inputs/nested_folder test_inputs

python src/joplin_custom_importer.py test_inputs/clipto_backup_240401_105154.json --app clipto
python src/joplin_custom_importer.py test_inputs/Google\ Keep/ --app google_keep
python src/joplin_custom_importer.py test_inputs/todo_txt/examples_from_readme.txt --app todo_txt
python src/joplin_custom_importer.py test_inputs/todoist/Privates\ 🏡.csv --app todoist

# This is a local directory, because it contains user data.
if [ -d "tmp" ]; then
    python src/joplin_custom_importer.py tmp/nimbus_export_user/Food\ Original\ export\ from\ Nimbus/ --app nimbus_note
    python src/joplin_custom_importer.py tmp/simplenote/notes.zip --app simplenote
    # python src/joplin_custom_importer.py tmp/tiddlywiki/tiddlers.json --app tiddlywiki
fi
