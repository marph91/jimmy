#!/bin/sh

set -x  # echo the commands
set -e  # fail if any command fails

export PYTHONPATH="$PYTHONPATH:src"
python -m unittest discover -v --buffer
# TODO: https://stackoverflow.com/questions/43463273/python-m-doctest-ignores-files-with-same-names-in-different-directories
python -m doctest src/*.py src/**/*.py
