import io
from pathlib import Path
import platform
import stat
import tarfile
import zipfile

import requests


def download_pandoc(targetfolder: Path, version: str):
    # Don't use pypandoc.pandoc_download.download_pandoc(), since it fails often for macOS
    # and it doesn't work in docker.
    target_filename = "pandoc"
    match platform.system().lower():
        case "darwin":
            download_filename = f"pandoc-{version}-{platform.machine().lower()}-macOS.zip"
        case "linux":
            machine = (
                "amd64" if platform.machine().lower() == "x86_64" else platform.machine().lower()
            )
            download_filename = f"pandoc-{version}-linux-{machine}.tar.gz"
        case "windows":
            download_filename = f"pandoc-{version}-windows-x86_64.zip"
            target_filename += ".exe"
        case _:
            print(f"unsupported system: {platform.system().lower()}")

    if version == "latest":
        url = f"https://github.com/jgm/pandoc/releases/latest/download/{download_filename}"
    else:
        url = f"https://github.com/jgm/pandoc/releases/download/{version}/{download_filename}"

    response = requests.get(url)
    response.raise_for_status()

    success = False
    suffixes = [s.lower() for s in Path(download_filename).suffixes]
    if suffixes[-1] == ".zip":
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
            for file_ in zip_ref.infolist():
                if Path(file_.filename).stem == "pandoc":
                    file_.filename = Path(file_.filename).name  # don't extract parent folders
                    zip_ref.extract(file_, targetfolder)
                    success = True
                    break
    elif suffixes[-2:] == [".tar", ".gz"]:
        with tarfile.open(fileobj=io.BytesIO(response.content)) as tar_ref:
            for file_ in tar_ref.getmembers():
                if Path(file_.name).stem == "pandoc":
                    file_.name = Path(file_.name).name  # don't extract parent folders
                    tar_ref.extract(file_, targetfolder)
                    success = True
                    break
    else:
        print(f"unexpected filetype: {Path(download_filename).suffixes[-2:]}")

    if not success:
        print(f"Couldn't find pandoc binary in {download_filename}")

    if platform.system().lower() == "linux":
        filename = targetfolder / "pandoc"
        filename.chmod(filename.stat().st_mode | stat.S_IEXEC)  # Make file executable.

    # download copyright
    response = requests.get(
        "https://raw.githubusercontent.com/jgm/pandoc/refs/heads/main/COPYRIGHT"
    )
    response.raise_for_status()
    (targetfolder / "copyright.pandoc").write_bytes(response.content)


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
    # try:
    download_pandoc(version="3.10", targetfolder=targetfolder)
    # except Exception as exc:
    #     print("pandoc download failed: ", str(exc))
    #     exit(1)
    # try:
    #     download_one2html(targetfolder=targetfolder)
    # except Exception as exc:
    #     print("one2html download failed: ", str(exc))
    #     exit(1)
