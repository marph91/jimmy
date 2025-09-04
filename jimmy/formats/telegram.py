"""Convert Telegram chats to the intermediate format."""

import json
from pathlib import Path

from jimmy import common, converter, intermediate_format as imf


class Converter(converter.BaseConverter):
    accept_folder = True

    @common.catch_all_exceptions
    def convert_note(self, chat):
        title = chat["name"]
        self.logger.debug(f'Converting chat "{title}"')
        note_imf = imf.Note(title, source_application=self.format, original_id=str(chat["id"]))

        note_body = []
        for message in chat["messages"]:
            if message["type"] != "service" and message.get("action") == "create_group":
                note_imf.created = common.timestamp_to_datetime(int(message["date_unixtime"]))
            if message["type"] != "message":
                continue

            content = message.get("text", "")
            if (file_ := message.get("file")) is not None:
                if content:
                    content += "\n"
                file_md = f"![{message.get('file_name', '')}]({str(self.root_path / file_)})"
                note_imf.resources.append(
                    imf.Resource(self.root_path / file_, file_md, message.get("file_name"))
                )
                content += file_md
            message_time = common.timestamp_to_datetime(int(message["date_unixtime"]))
            note_body.append(
                f"{message_time.strftime('%Y-%m-%d %H:%M:%S')}, **{message['from']}**: {content}"
            )

            # update the updated time each message to get the timestamp
            # of the last message at the end
            note_imf.updated = message_time
        note_imf.body = "\n\n".join(note_body)

        self.root_notebook.child_notes.append(note_imf)

    def convert(self, file_or_folder: Path):
        input_json = json.loads((file_or_folder / "result.json").read_text(encoding="utf-8"))
        if "chats" not in input_json:
            self.logger.error('"chats" not found. Is this really a Telegram export?')
            return

        for chat in input_json["chats"]["list"]:
            self.convert_note(chat)
