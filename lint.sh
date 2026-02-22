#!/bin/sh

ruff check  # ruff first, because it's fastest
ruff check --select I  # sort inputs, see https://docs.astral.sh/ruff/formatter/#sorting-imports
mypy jimmy
pylint jimmy
