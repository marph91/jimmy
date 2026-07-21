#!/bin/sh

uv run ruff check  # ruff first, because it's fastest
uv run ruff check --select I  # sort inputs, see https://docs.astral.sh/ruff/formatter/#sorting-imports
uv run mypy src
uv run pylint src
