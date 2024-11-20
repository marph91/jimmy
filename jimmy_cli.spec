# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

# pypandoc: https://github.com/orgs/pyinstaller/discussions/8387
datas = [(".version", ".")]
datas += collect_data_files("anyblock_exporter")
datas += collect_data_files("pypandoc")


# Generate list of hidden imports
# hidden import for dynamically loaded modules "formats.*":
# - https://stackoverflow.com/a/77395744/7410886
# - https://stackoverflow.com/a/35805418/7410886
# - https://pyinstaller.org/en/stable/when-things-go-wrong.html#listing-hidden-imports
from pathlib import Path
def list_python_files(folder):
    file_list = []
    for file_ in folder.iterdir():
        if file_.suffix == ".py" and file_.name != "__init__.py":
            file_list.append(f"{folder.stem}.{file_.stem}")
    return file_list

hiddenimports = list_python_files(Path("src/formats"))


# Generate the executable name based on OS.
import platform
executable_name = f"jimmy-cli-{platform.system().lower()}"


a = Analysis(
    ['src/jimmy_cli.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

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
#     name='jimmy_cli',
# )
