#!/usr/bin/env python3
"""Generate Nuitka include modules list from jimmy/formats directory."""

from pathlib import Path
import sys

formats_dir = Path("jimmy/formats")
format_modules = []

for file in sorted(formats_dir.glob("*.py")):
    if file.name != "__init__.py":
        module_name = f"jimmy.formats.{file.stem}"
        format_modules.append(module_name)

# Generate command-line arguments
args = ["--include-module=" + module for module in format_modules]
print(" ".join(args))
