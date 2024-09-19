"""Convert Facebook posts and messages to the intermediate format."""

import datetime as dt
import json
from pathlib import Path

import common
import converter
import intermediate_format as imf


def fix_encoding_error(input_str: str) -> str:
    # https://stackoverflow.com/a/26492671/7410886
    return input_str.encode("latin1").decode("utf8")


def create_markdown_link(is_image: bool, title: str, uri: str) -> str:
    return f"{'!' * is_image}[{title}]({uri})"


def timestamp_to_date_str(timestamp_s: float | int) -> str:
    return dt.datetime.utcfromtimestamp(timestamp_s).strftime("%Y-%m-%d")


class Converter(converter.BaseConverter):
    accepted_extensions = [".zip"]

    def prepare_input(self, input_: Path) -> Path:
        return common.extract_zip(input_)

    def handle_markdown_links(self, body: str) -> tuple[list, list]:
        resources = []
        for link in common.get_markdown_links(body):
            if link.is_web_link or link.is_mail_link:
                continue  # keep the original links
            resource_path = self.root_path / link.url
            # resource
            resources.append(imf.Resource(resource_path, str(link), link.text))

        return resources, []

    #################################################################
    # posts
    #################################################################

    def handle_post_attachments(self, post_attachment_list):
        post_body = ""
        post_metadata: dict = {}
        for post_attachments in post_attachment_list:
            for post_attachment_datum in post_attachments["data"]:
                for (
                    post_attachment_key,
                    post_attachment_value,
                ) in post_attachment_datum.items():
                    match post_attachment_key:
                        case "external_context":
                            post_body += f"\n\n<{post_attachment_value['url']}>"
                        case "media":
                            media_uri = post_attachment_value["uri"]
                            post_body += create_markdown_link(
                                common.is_image(self.root_path / media_uri),
                                post_attachment_value.get("title", ""),
                                media_uri,
                            )
                        case "place":
                            common.try_transfer_dicts(
                                post_attachment_value.get("coordinate", {}),
                                post_metadata,
                                ["latitude", "longitude"],
                            )
                        case _:
                            self.logger.debug(
                                "Unknown post attachment attribute "
                                f"{post_attachment_datum}."
                            )
        return post_body, post_metadata

    def convert_posts(self):
        assert self.root_path is not None  # for mypy

        posts_files = list(
            (self.root_path / "your_facebook_activity/posts").glob("your_posts*.json")
        )
        if not posts_files:
            self.logger.info("Couldn't find json file for posts.")
            return

        posts_notebook = imf.Notebook("Posts")
        self.root_notebook.child_notebooks.append(posts_notebook)

        for posts_file in posts_files:
            for post in json.loads(posts_file.read_text(encoding="utf-8")):
                updated_time = dt.datetime.utcfromtimestamp(post["timestamp"])
                post_body = ""

                for post_datum in post["data"]:
                    for post_data_key, post_data_value in post_datum.items():
                        match post_data_key:
                            case "update_timestamp":
                                updated_time = dt.datetime.utcfromtimestamp(
                                    post_data_value
                                )
                            case "post":
                                post_body = fix_encoding_error(post_data_value)
                            case _:
                                self.logger.debug(
                                    f"Unknown post attribute {post_datum}."
                                )

                if post.get("title") is not None:
                    # Skip posts in other profiles.
                    # TODO: Are this all posts in other profiles?
                    # post_title = fix_encoding_error(post_title_raw)
                    continue
                post_title = (
                    f"{timestamp_to_date_str(post['timestamp'])}: {post_body[:80]}"
                )

                att_body, att_metadata = self.handle_post_attachments(
                    post.get("attachments", [])
                )
                post_body += att_body

                if not post_body:
                    self.logger.debug(
                        f"Skipping entry {post['timestamp']} - empty body."
                    )
                    continue

                resources, _ = self.handle_markdown_links(post_body)

                posts_notebook.child_notes.append(
                    imf.Note(
                        post_title,
                        post_body,
                        created=dt.datetime.utcfromtimestamp(post["timestamp"]),
                        updated=updated_time,
                        source_application=self.format,
                        **att_metadata,
                        tags=[imf.Tag(tag["name"]) for tag in post.get("tags", [])],
                        resources=resources,
                    )
                )

    #################################################################
    # messages
    #################################################################

    def get_message_content(self, message):
        message_content = ""
        for key, value in message.items():
            match key:
                case (
                    "call_duration"
                    | "ip"
                    | "is_geoblocked_for_viewer"
                    | "is_unsent"
                    | "missed"
                    | "sender_name"
                    | "timestamp_ms"
                ):
                    pass  # handled separately or ignored
                case "content":
                    message_content += value
                case "audio_files" | "files" | "videos":
                    for file_ in value:
                        message_content += f"[]({file_['uri']})\n"
                case "gifs" | "photos":
                    for image in value:
                        message_content += f"![]({image['uri']})\n"
                case "share":
                    # The links are included in the original message already.
                    # message_content += f"<{value['link']}>"
                    pass
                case "sticker":
                    message_content += f"![]({value['uri']})"
                case "reactions":
                    if isinstance(value, dict):
                        for reaction in value["reactions"]:
                            message_content += reaction + "\n"
                    elif isinstance(value, list):
                        for reaction in value:
                            message_content += reaction["reaction"] + "\n"
                    else:
                        self.logger.debug(f"Ignoring reaction {message}.")
                case _:
                    self.logger.debug(f"Unsupported message item {message}.")
        return message_content

    def convert_messages(self):
        # TODO
        # pylint: disable=too-many-locals
        assert self.root_path is not None  # for mypy

        messages_notebook = imf.Notebook("Messages")
        self.root_notebook.child_notebooks.append(messages_notebook)

        for conversation in (
            self.root_path / "your_facebook_activity/messages/inbox"
        ).iterdir():
            conversation_files = list(conversation.glob("message_*.json"))
            if not conversation_files:
                self.logger.debug(f"No messages in {conversation.name}.")
                continue

            for file_index, conversation_file in enumerate(conversation_files):
                # Keep the split of json files to prevent too large markdown files.
                # (10000 messages per file)
                conversation_json = json.loads(
                    conversation_file.read_text(encoding="utf-8")
                )
                if len(conversation_json.get("participants", [])) > 2:
                    self.logger.debug(
                        f"Skipping group conversation {conversation.name}."
                    )
                    continue

                messages = conversation_json.get("messages")

                if messages is None:
                    self.logger.debug(f"No messages in {conversation_file}.")
                    continue

                note_body = []
                current_date = None
                for message in messages:
                    message_date = timestamp_to_date_str(message["timestamp_ms"] / 1000)
                    if current_date is None or message_date != current_date:
                        current_date = message_date
                        note_body.append(f"## {message_date}")
                    sender = (
                        fix_encoding_error(message["sender_name"])
                        if message["sender_name"]
                        else "Unknown"
                    )

                    message_content = self.get_message_content(message)
                    note_body.append(
                        f"**{sender}**: {fix_encoding_error(message_content)}"
                    )
                note_body_str = "\n\n".join(note_body)

                title = (
                    fix_encoding_error(conversation_json["title"])
                    if conversation_json["title"]
                    else "Unknown"
                )
                if file_index != 0:
                    title = f"{title} ({file_index})"

                resources, _ = self.handle_markdown_links(note_body_str)

                messages_notebook.child_notes.append(
                    imf.Note(
                        title,
                        note_body_str,
                        source_application=self.format,
                        resources=resources,
                    )
                )

    def convert(self, file_or_folder: Path):
        self.root_path = self.prepare_input(file_or_folder)

        self.convert_posts()
        self.convert_messages()
