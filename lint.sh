#!/bin/sh

ruff check  # ruff first, because it's fastest
mypy jimmy
pylint jimmy
