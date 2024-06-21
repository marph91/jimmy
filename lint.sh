#!/bin/sh

ruff check  # ruff first, because it's fastest
mypy src
pylint src
