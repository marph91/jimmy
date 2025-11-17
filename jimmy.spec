# There are some pyinstaller internal classes.
# ruff: noqa: F821

import os
from pathlib import Path
import platform

from PyInstaller.utils.hooks import collect_data_files

# pypandoc: https://github.com/orgs/pyinstaller/discussions/8387
datas = []
datas += collect_data_files("anyblock_exporter")
datas += [("bin", "bin")]  # pandoc and one2html


# Generate list of hidden imports
# hidden import for dynamically loaded modules "formats.*":
# - https://stackoverflow.com/a/77395744/7410886
# - https://stackoverflow.com/a/35805418/7410886
# - https://pyinstaller.org/en/stable/when-things-go-wrong.html#listing-hidden-imports
def list_python_files(folder):
    file_list = []
    for file_ in folder.iterdir():
        if file_.suffix == ".py" and file_.name != "__init__.py":
            file_list.append(f"jimmy.{folder.stem}.{file_.stem}")
    return file_list


hiddenimports = list_python_files(Path("jimmy/formats"))


# Generate the executable name based on OS.
system = platform.system().lower()
print("libc:", platform.libc_ver())

# need to correspond to ".github/workflows/build.yml"
match os.getenv("RUNNER_MACHINE"):
    case "windows-latest" | "ubuntu-22.04":
        pass  # default - nothing to do
    case "ubuntu-latest":
        # Differentiate between old glibc (above, for maximum compatibility)
        # and newer glibc (here, just for testing).
        system += "-new-glibc"
    case "ubuntu-22.04-arm":
        system += "-" + platform.machine().lower()
    case "macos-latest" | "macos-15-intel":
        # Differentiate between ARM and Intel based Macs.
        system += "-" + platform.machine().lower()
executable_name = f"jimmy-{system}"


a = Analysis(
    ["jimmy/jimmy_cli.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    # Optimization of the exe has almost no effect. Just apply it at analysis.
    # https://pyinstaller.org/en/stable/feature-notes.html#optimization-setting-in-the-spec-file
    optimize=2,
)
pyz = PYZ(a.pure)


def sort_by_size(files):
    files_with_sizes = []
    for file_ in files:
        if Path(file_[1]).is_file():
            files_with_sizes.append((Path(file_[1]).stat().st_size / 2**20, file_[1]))
        else:
            files_with_sizes.append((0.0, file_[1]))
    return tuple(reversed(sorted(files_with_sizes)))


print("-" * 100)
for file_ in sort_by_size(a.scripts):
    print(file_)
print("-" * 100)
for file_ in sort_by_size(a.binaries):
    print(file_)
print("-" * 100)
for file_ in sort_by_size(a.datas):
    print(file_)
print("-" * 100)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=executable_name,
    debug=False,
    bootloader_ignore_signals=False,
    # Strip unneeded libs. Not recommended for windows.
    # https://pyinstaller.org/en/stable/usage.html#cmdoption-s
    strip=platform.system().lower() != "windows",
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# only needed for size analysis
# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.datas,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     name='jimmy',
# )
