# shellcheck shell=bash
# shellcheck disable=SC2068
# jimmy executable can't be quoted

bats_require_minimum_version 1.5.0

# environment variables

if [[ ! -n "$TEST_CONTEXT" ]]; then
  echo "Please set 'TEST_CONTEXT' to 'binary' or 'docker'"
  exit 1
fi;

TEST_DATA_DIR=./data/test_data
if [[ "$TEST_CONTEXT" == "docker" ]]; then
  JIMMY_IMAGE=marphux/jimmy
  TEST_INPUT_DIR=/data/input  # inside docker
elif [[ "$TEST_CONTEXT" == "binary" ]]; then
  JIMMY_COMMAND=("../dist/jimmy*")
  TEST_INPUT_DIR="$TEST_DATA_DIR"  # in host system
else
  echo "Unsupported 'TEST_CONTEXT'"
  exit 1
fi
DEFAULT_OUTPUT_FOLDER="$(mktemp -d)/smoke_test_bats_tmp"
REFERENCE_DATA_DIR=./data/reference_data

# setup and teardown

setup_file() {
  mkdir -p "$DEFAULT_OUTPUT_FOLDER"
}

setup() {
  TEST_OUTPUT_FOLDER="$DEFAULT_OUTPUT_FOLDER/$BATS_TEST_NAME"
  mkdir -p "$TEST_OUTPUT_FOLDER"

  if [[ -n "$JIMMY_IMAGE" ]]; then
    JIMMY_EXTRA_ARGS=(--stdout-log-level DEBUG --output-folder /data/output)

    # mount some volumes if the executable is a docker container
    JIMMY_COMMAND=("docker" "run" "--user" "$(id -u):$(id -g)" "-v" "$TEST_DATA_DIR:$TEST_INPUT_DIR" "-v" "$TEST_OUTPUT_FOLDER:/data/output" "$JIMMY_IMAGE")
  elif [[ -n "${JIMMY_COMMAND[*]}" ]]; then
    JIMMY_EXTRA_ARGS=(--stdout-log-level DEBUG --output-folder "$TEST_OUTPUT_FOLDER")
  else
    false  # need either JIMMY_IMAGE or JIMMY_COMMAND
  fi
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
  run ! ${JIMMY_COMMAND[@]} cli "dsadsadsafadffasdasdsafsfdsafsdfdsafdasfdsfafsd" "${JIMMY_EXTRA_ARGS[@]}"
}

@test "default pandoc converter" {
  ${JIMMY_COMMAND[@]} cli "$TEST_INPUT_DIR/default_format/arbitrary_folder" "${JIMMY_EXTRA_ARGS[@]}"
  diff "$TEST_OUTPUT_FOLDER" "$REFERENCE_DATA_DIR/default_format/single_folder"
}

@test "frontmatter module (parsing and writing)" {
  ${JIMMY_COMMAND[@]} cli "$TEST_INPUT_DIR/obsidian/test_1_frontmatter/vault" --format obsidian --frontmatter joplin "${JIMMY_EXTRA_ARGS[@]}"
  diff --strip-trailing-cr "$TEST_OUTPUT_FOLDER" "$REFERENCE_DATA_DIR/obsidian/test_1_frontmatter"
}

@test "filter - exclude tags" {
  ${JIMMY_COMMAND[@]} cli "$TEST_INPUT_DIR/obsidian/test_1_frontmatter" --format obsidian --exclude-tags "*" "${JIMMY_EXTRA_ARGS[@]}"
}

@test "filter - include notes with tags" {
  ${JIMMY_COMMAND[@]} cli "$TEST_INPUT_DIR/obsidian/test_1_frontmatter" --format obsidian --include-notes-with-tags "*" "${JIMMY_EXTRA_ARGS[@]}"
}

@test "filter - include notes" {
  ${JIMMY_COMMAND[@]} cli "$TEST_INPUT_DIR/obsidian/test_1_frontmatter" --format obsidian --include-notes "Second sample note" "Sample note" "${JIMMY_EXTRA_ARGS[@]}"
}

@test "textbundle converter called from bear converter" {
  ${JIMMY_COMMAND[@]} cli "$TEST_INPUT_DIR/bear/test_1_frontmatter/backup.bear2bk" --format bear --frontmatter joplin "${JIMMY_EXTRA_ARGS[@]}"
  diff "$TEST_OUTPUT_FOLDER" "$REFERENCE_DATA_DIR/bear/test_1_frontmatter"
}

@test "cryptography module and password" {
  ${JIMMY_COMMAND[@]} cli "$TEST_INPUT_DIR/colornote/test_1_frontmatter/colornote-20241014.backup" --format colornote --password 1234 --frontmatter joplin "${JIMMY_EXTRA_ARGS[@]}"
  diff "$TEST_OUTPUT_FOLDER" "$REFERENCE_DATA_DIR/colornote/test_1_frontmatter"
}

@test "sqlite3 module" {
  ${JIMMY_COMMAND[@]} cli "$TEST_INPUT_DIR/qownnotes/test_1/note_folder" --format qownnotes "${JIMMY_EXTRA_ARGS[@]}"
  diff "$TEST_OUTPUT_FOLDER" "$REFERENCE_DATA_DIR/qownnotes/test_1"
}

@test "pyyaml module" {
  ${JIMMY_COMMAND[@]} cli "$TEST_INPUT_DIR/rednotebook/test_2/RedNotebook-Backup-2024-09-15.zip" --format rednotebook "${JIMMY_EXTRA_ARGS[@]}"
  diff "$TEST_OUTPUT_FOLDER" "$REFERENCE_DATA_DIR/rednotebook/test_2"
}

@test "anytype module" {
  ${JIMMY_COMMAND[@]} cli "$TEST_INPUT_DIR/anytype/test_1/Anytype.20241112.175339.64" --format anytype "${JIMMY_EXTRA_ARGS[@]}"
}

@test "onenote conversion with bundled executable" {
  skip "onenote disabled for now"
  ${JIMMY_COMMAND[@]} cli "$TEST_INPUT_DIR/onenote/test_1_frontmatter/OneDrive_2025-09-28.zip" --format onenote "${JIMMY_EXTRA_ARGS[@]}"
}

@test "pdf_oxyde module" {
  ${JIMMY_COMMAND[@]} cli "$TEST_INPUT_DIR/default_format/pdf" "${JIMMY_EXTRA_ARGS[@]}"
  diff "$TEST_OUTPUT_FOLDER" "$REFERENCE_DATA_DIR/default_format/pdf"
}
