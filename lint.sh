#!/bin/sh

black --check src
flake8 src
mypy src
pylint src
