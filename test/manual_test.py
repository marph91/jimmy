"""Cross platform script to run some manual tests."""

from pathlib import Path
import subprocess
import sys


def main():
    app_cmd = ["python", "../src/jimmy_cli.py"]

    cache = Path("../.cache")
    # ruff: noqa: E501
    # fmt: off
    input_arguments = [
        [cache / "arbitrary_folder"],
        [cache / "arbitrary_folder", cache / "arbitrary_folder"],
        [cache / "bear/backup.bear2bk", "--format", "bear"],
        [cache / "bear/backup-2.bear2bk", "--format", "bear"],
        [cache / "cacher/cacher-export-202406182304.json", "--format" ,"cacher"],
        [cache / "cherrytree/cherry.ctb.ctd", "--format" ,"cherrytree"],
        [cache / "clipto/clipto_backup_240401_105154.json", "--format" ,"clipto"],
        [cache / "day_one/Day.One.zip", "--format" ,"day_one"],
        [cache / "dynalist/dynalist-backup-2024-04-12.zip", "--format" ,"dynalist"],
        [cache / "google_keep/takeout-20240401T160516Z-001.zip", "--format" ,"google_keep"],
        [cache / "google_keep/takeout-20240401T160556Z-001.tgz", "--format" ,"google_keep"],
        [cache / "joplin/29_04_2024.jex", "--format" ,"joplin"],
        [cache / "jrnl/myjournal.json", "--format" ,"jrnl"],
        [cache / "nimbus_note/Food", "--format" ,"nimbus_note"],
        [cache / "notion/7acd77c1-0197-44e3-9793-ae81ab520ac9_Export-badce82a-60e8-402e-a32d-b0d89dc601cb.zip", "--format" ,"notion"],
        [cache / "obsidian/obsidian_vault", "--format" ,"obsidian"],
        [cache / "qownnotes/qownnotes_folder", "--format" ,"qownnotes"],
        [cache / "rednotebook/data", "--format" ,"rednotebook"],
        [cache / "rednotebook/RedNotebook-Backup-2024-09-15.zip", "--format" ,"rednotebook"],
        [cache / "simplenote/notes.zip", "--format" ,"simplenote"],
        [cache / "standard_notes/Standard Notes Backup - Sun Apr 28 2024 12_56_55 GMT+0200.zip", "--format" ,"standard_notes"],
        [cache / "synology_note_station/notestation-test-books.nsx", "--format" ,"synology_note_station"],
        [cache / "synology_note_station/test.nsx", "--format" ,"synology_note_station"],
        [cache / "textbundle/Textbundle Example v1.textbundle/", "--format" ,"textbundle"],
        [cache / "textbundle/Textbundle Example v2.textbundle/", "--format" ,"textbundle"],
        [cache / "textbundle/example.textpack", "--format" ,"textbundle"],
        [cache / "tiddlywiki/tiddlyhost.json", "--format" ,"tiddlywiki"],
        [cache / "tomboy_ng/gnote/", "--format" ,"tomboy_ng"],
        [cache / "tomboy_ng/tomboy-ng/", "--format" ,"tomboy_ng"],
        [cache / "zim_md"],
        [cache / "zoho_notebook/Notebook_14Apr2024_1300_html.zip", "--format" ,"zoho_notebook"],
    ]
    # fmt:on
    output_folder = Path("tmp_output")
    output_folder.mkdir(exist_ok=True)
    for arguments in input_arguments:
        subprocess.run(
            app_cmd + [str(arg) for arg in arguments],
            stderr=sys.stderr,
            stdout=sys.stdout,
            cwd=output_folder,
        )


if __name__ == "__main__":
    main()
