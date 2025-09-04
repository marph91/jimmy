"""Terminal User Interface (TUI) for Jimmy."""

import datetime
import logging
from pathlib import Path
import types
import webbrowser

from rich.logging import RichHandler
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, HorizontalGroup
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import Button, DataTable, Footer, Label, RichLog, Select
from textual.worker import Worker, WorkerState

from textual_fspicker import FileOpen, FileSave, Filters, SelectDirectory
from textual_fspicker.file_dialog import FileFilter

import jimmy.common
import jimmy.main


class CustomButton(Button):
    """
    Behaves like textual's built-in button.
    Only doesn't highlight the text when focussed.
    """

    DEFAULT_CSS = """
    CustomButton {
        &:focus {
            text-style: bold;
        }
    }
    """


class HelpScreen(ModalScreen):
    BINDINGS = [("escape", "app.pop_screen", "Back")]

    CSS = """
    HelpScreen {
        align: center middle;
    }

    HelpScreen > Container {
        align: center middle;
        width: 80;
        height: 20;
        border: thick $background 80%;
        background: $surface;
    }

    HelpScreen > Container > HorizontalGroup {
        align: center middle;
    }

    HelpScreen > * > Button, Label {
        max-width: 100%;
        margin: 1;
    }
    """

    def __init__(self, *args, initial_string: str = "", **kwargs):
        super().__init__(*args, **kwargs)
        self.initial_string = initial_string

    def compose(self) -> ComposeResult:
        with Container():
            if self.initial_string:
                with HorizontalGroup():
                    yield Label(self.initial_string)
            with HorizontalGroup():
                yield Label(
                    "To raise a bug, open a feature request or ask a question, contact me by:"
                )
            with HorizontalGroup():
                yield CustomButton("Email", id="contact_email")
                yield CustomButton("Github", id="contact_github")
                yield CustomButton("Joplin Forum", id="contact_joplin")
                yield CustomButton("Obsidian Forum", id="contact_obsidian")
            with HorizontalGroup():
                yield Label("Please include the input file and log if possible.")
            with HorizontalGroup():
                yield CustomButton("Ok", id="ok")

    def on_button_pressed(self, event: Button.Pressed):
        match event.button.id:
            case "contact_email":
                # urllib.parse.urlunparse seems to always add // after mailto
                url_parts = [
                    "mailto:",
                    # obfuscate the mail at least a bit
                    "".join(["martin.d", "@", "andix", ".de"]),
                    "?subject=Jimmy: Conversion to Markdown&",
                    "body=Please attach input file and log.",
                ]
                webbrowser.open("".join(url_parts))
            case "contact_github":
                webbrowser.open("https://github.com/marph91/jimmy/issues")
            case "contact_joplin":
                webbrowser.open(
                    "https://discourse.joplinapp.org/t/jimmy-a-joplin-import-tool/38503"
                )
            case "contact_obsidian":
                webbrowser.open(
                    "https://forum.obsidian.md/t/jimmy-convert-your-notes-to-markdown/88685"
                )
            case "ok":
                self.app.pop_screen()


class SelectInputScreen(ModalScreen):
    """Ask the user to select inputs before starting the conversion."""

    # See https://textual.textualize.io/guide/screens/#__tabbed_4_1

    CSS = """
    SelectInputScreen {
        align: center middle;
    }

    SelectInputScreen > Container {
        align: center middle;
        width: 80;
        height: 15;
        border: thick $background 80%;
        background: $surface;
    }

    SelectInputScreen > Container > HorizontalGroup {
        align: center middle;
    }

    SelectInputScreen > * > Button, Label {
        margin: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Container():
            with HorizontalGroup():
                yield Label("Please select an input before starting the conversion.")
            with HorizontalGroup():
                yield CustomButton("Ok")

    def on_button_pressed(self, _event: Button.Pressed):
        self.app.pop_screen()


class LoggingConsole(RichLog):
    file = False
    console: Widget

    def print(self, content):
        self.write(content)

    def get_log(self) -> str:
        """Get the visible log as string."""
        return "\n".join(line.text for line in self.lines)


class JimmyApp(App):
    SCREENS = {"help_screen": HelpScreen}
    BINDINGS = [
        Binding(key="escape", action="quit", description="Quit", show=False),
        Binding(key="q", action="quit", description="Quit"),
        Binding(key="c", action="copy_log", description="Copy Log"),
        Binding(key="s", action="save_log", description="Save Log"),
        Binding(key="h", action="push_screen('help_screen')", description="Help"),
    ]
    CSS = """
    .border {
        border: round;
        align: left middle;
    }

    Button, DataTable, RichLog {
        margin-left: 1;
        margin-right: 1;
    }

    .input_label {
        background: $surface;
        color: $foreground;
        padding: 0 1;
        border: tall $border-blurred;
        height: 3;
        width: 1fr;
    }

    .log {
        height: 2fr;
    }

    .start_conversion {
        align: center middle;
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.available_formats = jimmy.common.get_available_formats()
        now = datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%SZ")
        self.output_folder = Path().cwd() / f"{now} - Jimmy Import"

        self.conversion_worker: Worker | None = None
        self.file_dialog_extensions = None

        # log to widget
        self.logging_console = LoggingConsole(id="logging_console")
        console_handler_formatter = logging.Formatter("%(message)s")
        console_handler = RichHandler(
            console=self.logging_console,  # type: ignore[arg-type]
            markup=True,
            show_path=False,
        )
        console_handler.setFormatter(console_handler_formatter)
        console_handler.setLevel("DEBUG")
        jimmy.main.setup_logging(custom_handlers=[console_handler])

    def compose(self) -> ComposeResult:
        hg = HorizontalGroup(
            Select(
                (("Default", None),) + tuple((f,) * 2 for f in self.available_formats),
                allow_blank=False,
                value=None,
                id="select_format",
            ),
            classes="border",
        )
        hg.border_title = "Input Format"
        yield hg
        hg = HorizontalGroup(
            DataTable(show_header=False, show_cursor=False),
            CustomButton("Add File", id="select_input_file"),
            CustomButton("Add Folder", id="select_input_folder"),
            CustomButton("Clear", id="clear_inputs"),
            id="select_inputs",
            classes="border",
        )
        hg.border_title = "Inputs"
        yield hg
        hg = HorizontalGroup(
            Label(str(self.output_folder), classes="input_label", id="output_folder"),
            CustomButton("Change Folder", id="select_output_folder"),
            classes="border",
        )
        hg.border_title = "Output Folder"
        yield hg
        yield HorizontalGroup(
            CustomButton("Start Conversion", id="start_conversion"),
            classes="start_conversion",
        )
        hg = HorizontalGroup(self.logging_console, classes="border log")
        hg.border_title = "Log"
        yield hg
        yield Footer(show_command_palette=False)

    def on_mount(self):
        table = self.query_one(DataTable)
        table.add_column("Inputs", key="inputs")

    def on_select_changed(self, event: Select.Changed):
        if isinstance(event.select, FileFilter):
            return  # only handle options from format select
        file_dialog = self.query_one("#select_input_file")
        folder_dialog = self.query_one("#select_input_folder")
        # from select_format
        if event.value is None or event.value == Select.BLANK:
            file_dialog.disabled = False
            folder_dialog.disabled = False
            self.file_dialog_extensions = None
            return

        format_ = event.value
        accepted_inputs = self.available_formats[format_]

        # file
        if (accepted_extensions := accepted_inputs["accepted_extensions"]) is None:
            file_dialog.disabled = True
        else:
            file_dialog.disabled = False
            self.file_dialog_extensions = Filters(
                (
                    f"{format_} ({','.join(accepted_extensions)})",
                    lambda p: any(
                        p.suffix.lower() == accepted_extension
                        for accepted_extension in accepted_extensions
                    ),
                ),
            )
        # folder
        folder_dialog.disabled = not accepted_inputs["accept_folder"]

    def add_input(self, selected_input: Path | None):
        if selected_input is not None:
            table = self.query_one(DataTable)
            table.add_rows([[str(selected_input)]])

    def select_output_folder(self, selected_output_folder: Path | None):
        if selected_output_folder is not None:
            self.output_folder = selected_output_folder
            self.query_one("#output_folder").update(str(selected_output_folder))

    def on_worker_state_changed(self, event: Worker.StateChanged):
        if event.state == WorkerState.SUCCESS:
            assert self.conversion_worker is not None  # for mypy
            initial_string = (
                f"Conversion finished. Converted {self.conversion_worker.result}. "
                "Please check the files at the [link='"
                f"{self.output_folder.resolve().as_uri()}']output folder[/link]."
            )
            self.push_screen(HelpScreen(initial_string=initial_string))

    def on_button_pressed(self, event: Button.Pressed):
        match event.button.id:
            case "remove_input":
                assert event.button.parent is not None  # for mypy
                event.button.parent.remove()
            case "select_input_file":
                self.push_screen(
                    FileOpen(title="Select Output File", filters=self.file_dialog_extensions),
                    callback=self.add_input,
                )
            case "select_input_folder":
                self.push_screen(
                    SelectDirectory(title="Select Input File"), callback=self.add_input
                )
            case "clear_inputs":
                self.query_one(DataTable).clear()
            case "select_output_folder":
                self.push_screen(
                    SelectDirectory(title="Select Output Folder"),
                    callback=self.select_output_folder,
                )
            case "start_conversion":
                config = types.SimpleNamespace(
                    password=None,
                    frontmatter=None,
                    template_file=None,
                    global_resource_folder=None,
                    local_resource_folder=Path("."),
                    local_image_folder=None,
                    print_tree=False,
                    exclude_notes=None,
                    exclude_notes_with_tags=None,
                    exclude_tags=None,
                    include_notes=None,
                    include_notes_with_tags=None,
                    include_tags=None,
                )

                config.format = self.query_one("#select_format").selection

                table = self.query_one(DataTable)
                inputs = [Path(cell) for cell in table.get_column("inputs")]
                config.input = inputs

                if inputs == []:
                    self.push_screen(SelectInputScreen())
                    return

                config.output_folder = self.output_folder

                self.logging_console.clear()
                self.conversion_worker = self.run_worker(
                    lambda: jimmy.main.run_conversion(config),
                    name="jimmy_conversion",
                    thread=True,
                )

    def _action_copy_log(self):
        """Copy log to clipboard."""
        log_text = self.query_one("#logging_console").get_log()
        self.copy_to_clipboard(log_text)

    def _action_save_log(self):
        """Save log to file."""

        def save_log_to_file(log_file: Path | None):
            if log_file is not None:
                log_file.write_text(self.query_one("#logging_console").get_log())

        now = datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%SZ")
        self.push_screen(
            FileSave(
                title="Save Log to File",
                default_file=self.output_folder.parent / f"{now}_jimmmy_log.txt",
            ),
            callback=save_log_to_file,
        )


def main():
    JimmyApp().run()


if __name__ == "__main__":
    main()
