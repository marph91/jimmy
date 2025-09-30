from pathlib import Path
import platform
import stat

from pypandoc.pandoc_download import download_pandoc
import requests


def download_one2html(
    targetfolder: Path | None,
    version: str = "latest",
):
    match platform.system().lower():
        case "darwin":
            download_filename = f"one2html-darwin-{platform.machine().lower()}"
            target_filename = "one2html"
        case "linux":
            download_filename = "one2html-linux"
            target_filename = "one2html"
        case "windows":
            download_filename = "one2html-windows.exe"
            target_filename = "one2html.exe"
        case _:
            print(f"unsupported system: {platform.system().lower()}")

    if version == "latest":
        url = f"https://github.com/marph91/onenote.rs.exe/releases/latest/download/{download_filename}"
    else:
        url = f"https://github.com/marph91/onenote.rs.exe/releases/download/{version}/{download_filename}"

    response = requests.get(url)
    response.raise_for_status()
    filename = targetfolder / target_filename
    filename.write_bytes(response.content)

    if platform.system().lower() == "linux":
        filename.chmod(filename.stat().st_mode | stat.S_IEXEC)  # Make file executable.


if __name__ == "__main__":
    targetfolder = (Path(__file__).parent / "bin").resolve()
    targetfolder.mkdir(exist_ok=True)
    try:
        download_pandoc(version="3.8.1", targetfolder=targetfolder)
    except Exception:
        print("pandoc download failed")
    try:
        download_one2html(targetfolder=targetfolder)
    except Exception:
        print("one2html download failed")
