"""GUI for jimmy."""

from dataclasses import dataclass
import functools
from pathlib import Path
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk

import api_helper
import common
import jimmy


@dataclass
class Config:
    input: list[Path]
    format: str | None
    clear_notes: bool
    dry_run: bool
    log_file: bool
    stdout_log_level: str = "INFO"


def main():
    # It's ok to be more verbose when defining the GUI.
    # pylint: disable=too-many-locals,too-many-statements

    root = tk.Tk()
    style = ttk.Style()
    style.theme_use("clam")
    root.resizable(False, False)
    root.title("Jimmy")

    row = 0

    # row
    open_file_or_folder_label = ttk.Label(root, text="Open")
    open_file_or_folder_label.grid(column=0, row=row, sticky="w")

    file_or_folder_var = tk.StringVar()

    def select_file():
        file_ = filedialog.askopenfilename(title="Open File")
        file_or_folder_var.set(file_)

    open_file_button = ttk.Button(root, text="File", command=select_file)
    open_file_button.grid(column=1, row=row, sticky="nswe")

    def select_folder():
        folder = filedialog.askdirectory(title="Open Folder")
        file_or_folder_var.set(folder)

    open_folder_button = ttk.Button(root, text="Folder", command=select_folder)
    open_folder_button.grid(column=2, row=row, sticky="nswe")

    # row
    row += 1

    selected_file_or_folder_label = ttk.Label(root, text="Selected File/Folder")
    selected_file_or_folder_label.grid(column=0, row=row, sticky="w")

    open_file_or_folder_entry = ttk.Entry(root, textvariable=file_or_folder_var)
    open_file_or_folder_entry.grid(column=1, row=row, columnspan=2, sticky="nswe")

    # row
    row += 1

    format_label = ttk.Label(root, text="Format")
    format_label.grid(column=0, row=row, sticky="w")

    format_var = tk.StringVar()
    format_var.set("Default")
    choices = ["Default", *common.get_available_formats()]
    format_option_menu = ttk.OptionMenu(root, format_var, choices[0], *choices)
    format_option_menu.grid(column=1, row=row, columnspan=2, sticky="nswe")

    # separator = ttk.Separator(root, orient="horizontal")
    # row += 1
    # separator.grid(column=0, row=row, columnspan=2, sticky="ew")

    # row
    row += 1

    options_label = ttk.Label(root, text="Options")
    options_label.grid(column=0, row=row, rowspan=3, sticky="w")

    clear_notes_var = tk.BooleanVar()
    clear_notes_checkbox = ttk.Checkbutton(
        root, text="Clear Notes", variable=clear_notes_var
    )
    clear_notes_checkbox.grid(column=1, row=row, columnspan=2, sticky="nswe")

    # row
    row += 1

    dry_run_var = tk.BooleanVar()
    dry_run_checkbox = ttk.Checkbutton(root, text="Dry Run", variable=dry_run_var)
    dry_run_checkbox.grid(column=1, row=row, columnspan=2, sticky="nswe")

    # row
    row += 1

    log_file_var = tk.BooleanVar()
    log_file_checkbox = ttk.Checkbutton(
        root, text="Create Log File", variable=log_file_var
    )
    log_file_checkbox.grid(column=1, row=row, columnspan=2, sticky="nswe")

    # separator = ttk.Separator(root, orient="horizontal")
    # row += 1
    # separator.grid(column=0, row=row, columnspan=2, sticky="ew")

    # row
    row += 1

    def do_import():
        file_or_folder = file_or_folder_var.get()
        if file_or_folder == "" or not Path(file_or_folder).exists():
            tk.messagebox.showerror(
                "Import Failed", "Please select a valid file or folder"
            )
            return
        # support single input only for now
        format_ = None if format_var.get() == "Default" else format_var.get()
        config = Config(
            [Path(file_or_folder)],
            format_,
            clear_notes_var.get(),
            dry_run_var.get(),
            log_file_var.get(),
        )

        jimmy.setup_logging(config.log_file, config.stdout_log_level)

        if config.dry_run:
            api = None
        else:
            # create the connection to Joplin first to fail fast in case of a problem
            api = api_helper.get_api(
                functools.partial(tk.messagebox.showinfo, "API Connection"),
                functools.partial(tk.messagebox.showerror, "API Connection Failed"),
            )
            if api is None:
                return

        if config.clear_notes and not config.dry_run:
            delete_everything = tk.messagebox.askyesno(
                message="Really clear everything and start from scratch?"
                "\nThis may take some time."
            )
            if not delete_everything:
                return

        stats = jimmy.jimmy(api, config)
        tk.messagebox.showinfo("Import Succeeded", f"Imported {stats}")

    import_button = ttk.Button(text="Import", command=do_import)
    import_button.grid(column=0, row=row, columnspan=3, sticky="nswe")

    # make the grid cells adaptive to the window size
    root.grid_rowconfigure(tuple(i for i in range(row)), weight=1)
    root.grid_columnconfigure(tuple(i for i in range(3)), weight=1)

    root.mainloop()


if __name__ == "__main__":
    main()
