# shellcheck shell=bash

bats_require_minimum_version 1.5.0

# environment variables

JIMMY_EXE="../dist/jimmy*"
DEFAULT_OUTPUT_FOLDER="$(mktemp -d)/smoke_test_bats_tmp"
TEST_DATA_DIR=./data/test_data/

# setup and teardown

setup_file() {
  mkdir -p "$DEFAULT_OUTPUT_FOLDER"
}

setup() {
  TEST_OUTPUT_FOLDER="$DEFAULT_OUTPUT_FOLDER/$BATS_TEST_NAME"
  JIMMY_ARGS=(--stdout-log-level DEBUG --output-folder "$TEST_OUTPUT_FOLDER")
}

teardown() {
  if [ -d "$TEST_OUTPUT_FOLDER" ]; then
    ls -lhR "$TEST_OUTPUT_FOLDER"
  else
    echo "output folder $TEST_OUTPUT_FOLDER doesn't exist"
  fi
}

teardown_file() {
  rm -r "$DEFAULT_OUTPUT_FOLDER"
}

# tests

@test "non-existing folder" {
  # shellcheck disable=SC2086
  # jimmy executable can't be quoted
  run ! $JIMMY_EXE cli "dsadsadsafadffasdasdsafsfdsafsdfdsafdasfdsfafsd" "${JIMMY_ARGS[@]}"
}

@test "default pandoc converter" {
  $JIMMY_EXE cli "$TEST_DATA_DIR/default_format/arbitrary_folder" "${JIMMY_ARGS[@]}"
}

@test "frontmatter module" {
  $JIMMY_EXE cli "$TEST_DATA_DIR/obsidian/test_1_frontmatter" --format obsidian "${JIMMY_ARGS[@]}"
}

@test "filter - exclude tags" {
  $JIMMY_EXE cli "$TEST_DATA_DIR/obsidian/test_1_frontmatter" --format obsidian --exclude-tags "*" "${JIMMY_ARGS[@]}"
}

@test "filter - include notes with tags" {
  $JIMMY_EXE cli "$TEST_DATA_DIR/obsidian/test_1_frontmatter" --format obsidian --include-notes-with-tags "*" "${JIMMY_ARGS[@]}"
}

@test "filter - include notes" {
  $JIMMY_EXE cli "$TEST_DATA_DIR/obsidian/test_1_frontmatter" --format obsidian --include-notes "Second sample note" "Sample note" "${JIMMY_ARGS[@]}"
}

@test "textbundle converter called from bear converter" {
  $JIMMY_EXE cli "$TEST_DATA_DIR/bear/test_1_frontmatter/backup.bear2bk" --format bear "${JIMMY_ARGS[@]}"
}

@test "cryptography module and password" {
  $JIMMY_EXE cli "$TEST_DATA_DIR/colornote/test_1_frontmatter/colornote-20241014.backup" --format colornote --password 1234 "${JIMMY_ARGS[@]}"
}

@test "sqlite3 module" {
  $JIMMY_EXE cli "$TEST_DATA_DIR/qownnotes/test_1/note_folder" --format qownnotes "${JIMMY_ARGS[@]}"
}

@test "pyyaml module" {
  $JIMMY_EXE cli "$TEST_DATA_DIR/rednotebook/test_2/RedNotebook-Backup-2024-09-15.zip" --format rednotebook "${JIMMY_ARGS[@]}"
}

@test "anytype module" {
  $JIMMY_EXE cli "$TEST_DATA_DIR/anytype/test_1/Anytype.20241112.175339.64" --format anytype "${JIMMY_ARGS[@]}"
}

@test "onenote conversion with bundled executable" {
  skip "onenote disabled for now"
  $JIMMY_EXE cli "$TEST_DATA_DIR/onenote/test_1_frontmatter/OneDrive_2025-09-28.zip" --format onenote "${JIMMY_ARGS[@]}"
}
