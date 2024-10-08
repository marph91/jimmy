#!/bin/sh

set -x  # echo the commands
set -e  # fail if any command fails

export PYTHONPATH="$PYTHONPATH:src"
python -m unittest discover -v --buffer
python -m doctest src/*.py src/**/*.py
