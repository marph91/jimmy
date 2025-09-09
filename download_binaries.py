from pathlib import Path

from pypandoc.pandoc_download import download_pandoc


if __name__ == "__main__":
    targetfolder = (Path(__file__).parent / "bin").resolve()
    targetfolder.mkdir(exist_ok=True)
    try:
        download_pandoc(version="3.6.1", targetfolder=targetfolder)
    except Exception:
        print("pandoc download failed")
