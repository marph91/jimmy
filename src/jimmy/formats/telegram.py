"""
Convert Telegram chats to the intermediate format.

Based on Telegram Data Export Schema: <https://core.telegram.org/import-export>
"""

from collections import defaultdict
from datetime import datetime
import enum
from enum import auto
import json
from pathlib import Path
from typing import NamedTuple

from jimmy import common, converter, intermediate_format as imf
import jimmy.md_lib.conversations
import jimmy.md_lib.links


class Converter(converter.BaseConverter):
    # Telegram Message object `media_types`. Order defines precedence. If multiple media types are
    # present in a message, the first one encountered will be used as the primary media.
    MESSAGE_MEDIA_TYPES = [
        "photo",
        "video",
        "voice",
        "audio",
        "video_message",
        "animation",
        "sticker",
        "file",
    ]

    # Configurations for thumbnails, currently not externally configurable
    include_thumbnails = True
    inline_thumbnail = True
    use_image_thumbnails = False

    # Configurations for locations, currently not externally configurable
    include_locations = True

    # Configurations for contacts, currently not externally configurable
    include_contacts = True

    # Configurations for reactions, currently not externally configurable
    include_reactions = True

    json_fallback_ms: int | None = None
    file_map: dict[str, Path] | None = None


    referenced_messages: set[str] = set()

    def _convert_text_entities(self, text_entities: list) -> str:
        """Convert Telegram text_entities (MessageEntity) to Markdown."""

        if not text_entities:
            return ""

        parts = []

        for entity in text_entities:
            text = entity.get("text", "")

            match entity.get("type", "plain"):
                # ---- Basic formatting ----
                case TelegramMessageEntity.BOLD:
                    text = f"**{text}**"
                case TelegramMessageEntity.ITALIC:
                    text = f"*{text}*"
                case TelegramMessageEntity.UNDERLINE:
                    text = f"++{text}++"
                case TelegramMessageEntity.STRIKETHROUGH:
                    text = f"~~{text}~~"
                case TelegramMessageEntity.CODE:
                    text = f"`{text}`"
                case TelegramMessageEntity.PRE:
                    # code block - optionally preserve language if provided (not in schema)
                    text = f"\n```\n{text}\n```\n"

                # case "spoiler":
                # spoiler block - no native Markdown spoiler syntax
                # TODO: implement spoiler handling if Jimmy decides to support it

                # ---- Links and mentions ----
                case TelegramMessageEntity.TEXT_LINK:
                    url = entity.get("url", "")
                    text = jimmy.md_lib.links.make_link(text, url)
                case TelegramMessageEntity.MENTION_NAME:
                    user_id = entity.get("user_id", "")
                    text = jimmy.md_lib.links.make_link(text, f"tg://user?id={user_id}")

            # ---- Plain or already‐self‑descriptive types ----
            # mention, hashtag, bot_command, url, email, etc. are kept as plain text
            # because they are human‑readable markers.

            parts.append(text)

        return "".join(parts)

    def _handle_action(
        self, telegram_message: TelegramMessageWrapper
    ) -> tuple[str, list[imf.Resource]]:
        """
        Process service action messages.

        Returns (markdown_text, resources) for the action.
        """
        message, chat_id, chat_type = telegram_message

        action = message.get("action")

        if not action:
            return "", []

        actor = message.get("actor", "Someone")
        # actor_id = message.get("actor_id", None)

        # ---- Supported actions ----
        match action:
            case TelegramServiceMessageAction.PIN_MESSAGE:
                pinned_msg_id = message.get("message_id")

                if pinned_msg_id is None:
                    self.logger.warning("pin_message action missing message_id")

                    return "", []

                # Build an anchor that can be used in the final output.
                # If we have chat context, make it unique; otherwise fallback.
                anchor = generate_anchor(pinned_msg_id, chat_id=chat_id, chat_type=chat_type)

                self.referenced_messages.add(anchor)

                link = jimmy.md_lib.links.make_link("this message", f"#{anchor}", is_image=False)

                markdown = f"**{actor}** pinned {link}"

                return markdown, []

        # ---- Unknown actions ----
        # Log but still produce a descriptive line
        self.logger.debug(f"Unhandled service action: {action}")
        markdown = f"Service action: {action} (by {actor})"

        return markdown, []

    def _handle_media(
        self,
        message: dict,
        include_thumbnail: bool = True,
        inline_thumbnail: bool = True,
        use_image_thumbnails: bool = False,
    ) -> tuple[str, list[imf.Resource]]:
        """
        Detect media in the message and return (media_markdown, resources).

        Parameters:
            include_thumbnail (bool):
                If True, the thumbnail (if present) will be added as a separate
                Resource object. The file will be copied to the output folder.
            inline_thumbnail (bool):
                If True and a thumbnail is used as the link text, the thumbnail
                Resource will have its `original_text` set so the writer replaces
                the inline image placeholder. If False, the thumbnail is only
                attached as a resource without being embedded in the note body.
            use_image_thumbnails (bool):
                If True, thumbnails will also be used for image media. Normally,
                images are displayed directly; with this flag, the thumbnail
                becomes a clickable link to the full‑size image.

        Returns:
            (media_markdown, resources)
            - media_markdown: the Markdown string to insert into the note body.
            - resources: list of Resource objects to be written to disk.
        """

        media_path = None
        media_type = None

        for field in self.MESSAGE_MEDIA_TYPES:
            if field in message and message[field]:
                media_path = message[field]
                media_type = field

                break

        if not media_path:
            return "", []

        # ----- Main media -----
        # Get file name (might not be present for some types)
        file_name = message.get("file_name", Path(media_path).name)

        # Locate the file (fallback to root_path / media_path)
        resource_path = common.find_file_recursively(self.root_path, media_path) or (
            self.root_path / media_path
        )

        if not resource_path or not resource_path.exists():
            self.logger.warning(f"Media file not found: {media_path}")

            return "", []

        # Determine if it's an image (based on type or extension)
        is_image = media_type in ["photo", "sticker"] or common.is_image(resource_path)
        has_thumbnail = "thumbnail" in message and message["thumbnail"]

        resources = []

        # 1. Decide whether to include the thumbnail as a resource
        include_thumb_resource = (
            include_thumbnail and has_thumbnail and (not is_image or use_image_thumbnails)
        )

        # 2. Decide whether to use the thumbnail as the link text in the main marker
        #    This requires that we want to inline it (so the placeholder will be replaced)
        use_thumbnail_for_marker = include_thumb_resource and inline_thumbnail

        # 3. Create the thumbnail resource if requested
        thumb_marker = None
        if include_thumb_resource:
            thumb_path = message["thumbnail"]
            thumb_resource_path = common.find_file_recursively(self.root_path, thumb_path) or (
                self.root_path / thumb_path
            )

            thumb_marker = jimmy.md_lib.links.make_link(
                "Thumbnail", str(thumb_resource_path), is_image=True
            )
            thumb_name = f"thumbnail_{Path(thumb_path).name}"

            thumb_resource = imf.Resource(
                filename=thumb_resource_path,
                original_text=thumb_marker if inline_thumbnail else None,
                title=thumb_name,
            )

            resources.append(thumb_resource)

        # 4. Build the main media marker
        if use_thumbnail_for_marker:
            # Use the thumbnail as a clickable link to the main media
            main_marker = jimmy.md_lib.links.make_link(
                str(thumb_marker), str(resource_path), is_image=False
            )
            main_title = thumb_marker
        else:
            main_marker = jimmy.md_lib.links.make_link(
                file_name, str(resource_path), is_image=is_image
            )
            main_title = file_name

        # 5. Create the main media resource
        main_resource = imf.Resource(
            filename=resource_path,
            original_text=main_marker,
            title=main_title,
        )

        # Insert main resource first (so it's processed before the thumbnail)
        resources.insert(0, main_resource)

        return main_marker, resources

    def _handle_location(self, message: dict) -> tuple[str, list[str]]:
        """
        Process location_information from a message.

        Returns:
            (extra_markdown, tags_to_add)
        """
        if "location_information" not in message:
            return "", []

        location = message["location_information"]
        latitude = location.get("latitude")
        longitude = location.get("longitude")

        if latitude is None or longitude is None:
            return "", []

        extra = f"\n\n📍 Location: {latitude:.6f}, {longitude:.6f}"

        return extra, ["location"]

    def _handle_contact(self, message: dict) -> tuple[str, list[imf.Resource]]:
        """
        Process contact_information and contact_vcard from a message.

        Returns:
            (extra_markdown, list_of_resources)
        """
        if "contact_information" not in message and "contact_vcard" not in message:
            return "", []

        contact_info = message.get("contact_information", {})
        vcard_rel = message.get("contact_vcard")

        first = contact_info.get("first_name", "")
        last = contact_info.get("last_name", "")
        phone = contact_info.get("phone_number", "")
        name = f"{first} {last}".strip() or "Unknown"

        # Build descriptive line
        contact_line = f"📇 Contact: {name}"

        if phone:
            contact_line += f" (phone: {phone})"

        resources = []

        # Generate the vCard Jimmy intermediate resource
        if vcard_rel:
            vcard_path = self._locate_resource(vcard_rel)

            if vcard_path is not None:
                vcard_marker = jimmy.md_lib.links.make_link(
                    Path(vcard_rel).name, str(vcard_path), is_image=False
                )

                contact_line += f" (vCard: {vcard_marker})"

                vcard_resource = imf.Resource(
                    filename=vcard_path,
                    original_text=vcard_marker,
                    title=Path(vcard_rel).name,
                )

                resources.append(vcard_resource)
            else:
                self.logger.warning(f"vCard file not found: {vcard_rel}")

                contact_line += f" ((vCard: {vcard_rel} (missing))"

        extra = f"\n\n{contact_line}"

        return extra, resources

    def _handle_reactions(self, message: dict) -> tuple[str, dict[str, list]]:
        """
        Process reactions from a message.

        Returns:
            (extra_markdown, reactions_data_dict)
        """
        reactions_data = message.get("reactions")
        if not reactions_data:
            return "", {}

        parts = []
        for reaction in reactions_data:
            emoji = reaction.get("emoji", "")
            count = reaction.get("count", 0)
            recent = reaction.get("recent", [])
            reactors = [u.get("from", "?") for u in recent[:3]]
            reactor_str = ", ".join(reactors) if reactors else ""

            if count > 1 and reactor_str:
                parts.append(f"{emoji} ({count}) - {reactor_str}")
            elif count == 1 and reactor_str:
                parts.append(f"{emoji} - {reactor_str}")
            else:
                parts.append(f"{emoji} ({count})")

        if not parts:
            return "", {}

        extra = "\n\nReactions: " + " | ".join(parts)

        return extra, {"reactions": reactions_data}  # wrap for frontmatter

    def _process_message(
        self,
        telegram_message: TelegramMessageWrapper,
        include_location: bool = True,
        include_contact: bool = True,
        include_reactions: bool = True,
    ) -> tuple[str, list[imf.Resource], list[str], dict[str, list[dict]]]:
        """
        Process a single message, returning (full_content, resources, tags, frontmatter_extra).

        Parameters:
            include_location (bool):
                If True, parse and include location data from `location_information`.
            include_contact (bool):
                If True, parse and include contact data from `contact_information`
                and attach the `.vcard` file if present.
            include_reactions (bool):
                If True, parse and include reaction summaries and return the raw
                reaction data in the `frontmatter_extra` dict.
        """
        message = telegram_message.message

        # 1. Basic text content
        # Get the rich text if available
        if "text_entities" in message:
            content = self._convert_text_entities(message["text_entities"])
        else:
            # Fallback to plain text (for older exports or simple messages)
            content = message.get("text", "")

        # 2. Handle media
        media_markdown, media_resources = self._handle_media(
            message, self.include_thumbnails, self.inline_thumbnail, self.use_image_thumbnails
        )

        # ---- 2.5 Handle service action ----
        action_markdown, action_resources = self._handle_action(telegram_message)

        if action_markdown:
            content += f"{content}\n\n{action_markdown}" if content else action_markdown

        # Combine text and media (choose your preferred formatting)
        if content and media_markdown:
            # media first, text as caption (blockquote)
            caption = "\n".join(f"> {line}" for line in content.splitlines())
            full_content = f"{media_markdown}\n\n{caption}"
        elif media_markdown:
            full_content = media_markdown
        else:
            full_content = content

        # 3. Tags from inline #hashtags
        # Extract tags from the original text (before media markdown)
        tags = jimmy.md_lib.tags.get_inline_tags(content, ["#"])

        # --- Initialize optional extras with safe defaults ---
        location_extra = ""
        contact_extra = ""
        reactions_extra = ""
        contact_resources: list[imf.Resource] = []
        reactions_frontmatter: dict[str, list] = {}

        # 4. Handle location
        if include_location:
            location_extra, location_tags = self._handle_location(message)

            tags.extend(location_tags)

        # 5. Handle contact
        if include_contact:
            contact_extra, contact_resources = self._handle_contact(message)

        # 6. Handle reactions
        if include_reactions:
            reactions_extra, reactions_frontmatter = self._handle_reactions(message)

        # 7. Assemble final content and resources
        full_content += location_extra + contact_extra + reactions_extra
        resources = media_resources + contact_resources + action_resources

        return full_content, resources, tags, reactions_frontmatter

    def _get_message_datetime(self, message: dict) -> datetime:
        """Extract Telegram message datetime."""

        # 1. Primary: unixtime (most reliable)
        if "date_unixtime" in message:
            return common.timestamp_to_datetime(int(message["date_unixtime"]))

        # 2. Secondary: ISO date string
        if "date" in message:
            try:
                return common.iso_to_datetime(message["date"])
            except ValueError, TypeError:
                pass  # fall through

        self.logger.warning(
            "Neither 'date' nor 'date_unixtime' found, converter might need to be updated."
        )

        # 3. Tertiary: filesystem mtime of the associated media file
        if self.file_map is not None:
            for field in self.MESSAGE_MEDIA_TYPES:
                if field in message and message[field]:
                    media_rel_path = message[field]
                    media_path = self._locate_resource(media_rel_path)

                    if media_path is not None:
                        ts_ms = common.get_ctime_mtime_ms(media_path).get("updated")

                        if ts_ms:
                            return common.timestamp_to_datetime(ts_ms / 1000.0)

                    break  # we found a media field; no need to check others

        # 4. Quaternary: mtime of the result.json (global fallback)
        if self.json_fallback_ms is not None:
            return common.timestamp_to_datetime(self.json_fallback_ms / 1000.0)

        # 5. Last resort: current time (should rarely happen)
        self.logger.warning("No timestamp found for message, using current time.")
        return common.timestamp_to_datetime(common.current_unix_ms() / 1000.0)

    def _locate_resource(self, rel_path: str) -> Path | None:
        """Locate an existing resource file in root_path, using the file_map if available."""

        if self.file_map and rel_path in self.file_map:
            candidate = self.file_map[rel_path]
        else:
            candidate = self.root_path / rel_path

        return candidate if candidate.exists() else None

    def _build_file_map(self, root_path: Path) -> dict[str, Path]:
        """Build a file map for quick lookup."""

        file_map = {}

        for file_path in root_path.rglob("*"):
            if file_path.is_file():
                rel = file_path.relative_to(root_path)
                file_map[str(rel)] = file_path
                # also by filename for loose exports
                file_map[file_path.name] = file_path

        return file_map

    def _build_note_from_messages(
        self,
        messages: list[tuple[datetime, TelegramMessageWrapper]],
        title: str,
        original_id: str,
        chat_id: int,
        *,
        extra_frontmatter: dict | None = None,
    ) -> imf.Note | None:
        """Create a Note from a sorted list of (datetime, message) tuples."""

        if not messages:
            return None

        first_date = messages[0][0]
        last_date = messages[-1][0]

        note = imf.Note(title, source_application=self.format, original_id=original_id)
        note.created = first_date
        note.updated = last_date

        md_conversation = jimmy.md_lib.conversations.Conversation()
        resources = []
        all_tags = []
        all_reactions = []

        for _, telegram_message in messages:

            content, res, tags, reactions = self._process_message(
                telegram_message,
                include_location=self.include_locations,
                include_contact=self.include_contacts,
                include_reactions=self.include_reactions,
            )

            message_type = telegram_message.message.get("type")

            if message_type == TelegramMessageType.SERVICE:
                message_author = "System"
            else:
                message_author = telegram_message.message.get("from", "Unknown")

            message_time = self._get_message_datetime(telegram_message.message)
            message_prefix = message_time.strftime("%Y-%m-%d %H:%M:%S")


            # Handle additional anchors from note links
            if telegram_message.anchor in self.referenced_messages:
                message_id = telegram_message.message.get("id")

                self.logger.debug(f"Adding anchor for message {message_id}")

                # <a id="section_id"></a>
                message_prefix=f"""<a id="{telegram_message.anchor}"></a>\n{message_prefix}"""


            md_message = jimmy.md_lib.conversations.Message(
                message_author,
                content,
                prefix=message_prefix,
            )

            # md_message.attachment_links.extend(resource.original_text for resource in res)
            md_conversation.messages.append(md_message)

            resources.extend(res)
            all_tags.extend(tags)

            # TODO: decide if this is necessary
            if reactions:
                all_reactions.append(reactions)

        note.body = md_conversation.to_md()
        note.resources = resources
        note.tags = [imf.Tag(tag) for tag in dict.fromkeys(all_tags)]

        if self.include_locations:
            # If there is at least one location, set note.latitude/longitude from first occurrence
            for _, (message, _, _) in messages:
                if "location_information" in message:
                    note.latitude = message["location_information"].get("latitude")
                    note.longitude = message["location_information"].get("longitude")

                    break

        if not note.body and not note.resources and not note.tags:
            self.logger.debug("Skipping empty chat.")

            return None

        frontmatter = {
            "chat_id": chat_id,
            "message_count": len(messages),
            "created": first_date.isoformat(),
            "updated": last_date.isoformat(),
        }

        if all_reactions:
            frontmatter["reactions"] = all_reactions

        if extra_frontmatter:
            frontmatter.update(extra_frontmatter)

        note.frontmatter = frontmatter

        return note

    def _register_references(
        self, message: dict, chat_id = int | None, chat_type = str | None
    ) -> None:
        """
        Process messages registering all internal references to other telegram chats/messages.

        TODO: Currently only implemented pin message action references, others to be implemented.
        """
        action = message.get("action")

        if not action:
            return

        # actor_id = message.get("actor_id", None)

        # ---- Supported actions ----
        match action:
            case TelegramServiceMessageAction.PIN_MESSAGE:
                pinned_msg_id = message.get("message_id")

                if pinned_msg_id is None:
                    self.logger.warning("pin_message action missing message_id")

                    return

                anchor = generate_anchor(pinned_msg_id, chat_id=chat_id, chat_type=chat_type)

                self.referenced_messages.add(anchor)

                return

        # ---- Unknown actions ----
        # Not handled right now

        return

    @common.catch_all_exceptions()
    def convert_note(self, chat: TelegramChat):
        chat_id, chat_name, chat_type, chat_messages = chat

        if chat_type == TelegramChatType.SAVED_MESSAGES:
            title = "Saved Messages"
        else:
            title = chat_name or "Unnamed Chat"

        self.logger.debug(f'Converting chat "{title}"')

        messages = chat_messages or []

        # Filter out non‑message events and create list of (dt, msg)
        msg_tuples = []

        for message in messages:
            if message.get("type") not in TelegramMessageType:
                continue

            dt = self._get_message_datetime(message)
            telegram_message = TelegramMessageWrapper(message, chat_id, chat_type)
            msg_tuples.append((dt, telegram_message))

            # Register all internal messages references
            self._register_references(message, chat_id, chat_type)

        if not msg_tuples:
            self.logger.debug(f"No regular messages in chat '{title}', skipping.")

            return

        # Sort by datetime (should already be in order, but safe)
        msg_tuples.sort(key=lambda x: x[0])

        note = self._build_note_from_messages(
            msg_tuples,
            title=title,
            original_id=str(chat_id),
            chat_id=chat_id,
            extra_frontmatter={"chat_type": chat_type},
        )

        # Handle creation time from a service message if needed
        # (logic can add that be added before building or inside)
        if note is not None:
            self.root_notebook.child_notes.append(note)

    @common.catch_all_exceptions()
    def convert_saved_messages_grouped_by_day(self, chat: TelegramChat):
        chat_id, _, chat_type, chat_messages = chat

        if chat_type != TelegramChatType.SAVED_MESSAGES:
            self.logger.warning("This method is intended for 'saved_messages' chats only.")
            self.convert_note(chat)

            return

        messages_by_day = defaultdict(list)

        messages = chat_messages or []

        for message in messages:
            if message.get("type") not in TelegramMessageType:
                continue

            dt = common.timestamp_to_datetime(int(message["date_unixtime"]))
            telegram_message = TelegramMessageWrapper(message, chat_id, chat_type)
            messages_by_day[dt.date()].append((dt, telegram_message))

            # Register all internal messages references
            self._register_references(message, chat_id, chat_type)

        if not messages_by_day:
            self.logger.debug("No regular messages found in saved messages chat.")

            return

        for day, msg_list in messages_by_day.items():
            msg_list.sort(key=lambda x: x[0])  # already sorted, but ensure

            title = f"Saved Messages - {day.isoformat()}"

            note = self._build_note_from_messages(
                msg_list,
                title=title,
                original_id=f"{chat_id}_{day.isoformat()}",
                chat_id=chat_id,
                extra_frontmatter={"date": day.isoformat()},
            )

            if note:
                self.root_notebook.child_notes.append(note)
                self.logger.debug(f"Created note for {day}")

    def convert(self, file_or_folder: Path):
        json_path = file_or_folder / "result.json"

        if not json_path.exists():
            self.logger.error(f"result.json not found in {file_or_folder}")

            return

        # Store file `updated` property as instance variable for later use, if needed
        self.json_fallback_ms: int | None = common.get_ctime_mtime_ms(json_path).get("updated")
        self.file_map: dict[str, Path] | None = self._build_file_map(file_or_folder)

        input_json = json.loads(json_path.read_text(encoding="utf-8"))

        if (chats := input_json.get("chats")) is not None:
            self.logger.info('Found "chats" key. Assuming that this is a complete "DataExport".')

            for chat in chats["list"]:
                telegram_chat = TelegramChat(**chat)

                # Dispatch: if it's Saved Messages, group by day; otherwise use normal conversion
                if telegram_chat.type == TelegramChatType.SAVED_MESSAGES:
                    self.convert_saved_messages_grouped_by_day(telegram_chat)
                else:
                    self.convert_note(telegram_chat)
        else:
            self.logger.info('No "chats" key. Assuming that this is a single "ChatExport".')

            telegram_chat = TelegramChat(**input_json)

            # For a single export, check if it's Saved Messages
            if telegram_chat.type == TelegramChatType.SAVED_MESSAGES:
                self.convert_saved_messages_grouped_by_day(telegram_chat)
            else:
                self.convert_note(telegram_chat)


class TelegramChat(NamedTuple):
    """
    Represents a chat object from a Telegram Export Data file.

    This structure mirrors the chat metadata and its associated messages as
    defined in the Telegram chat export JSON schema. It is designed to be
    lightweight and immutable.

    Attributes:
        id (int): Unique identifier for this chat.
            **Important:** This number may have more than 32 significant bits.
            While it has at most 52 significant bits, some programming languages
            may have difficulty interpreting it. Use a signed 64-bit integer or
            double-precision float type to store this identifier safely.
        name (str | None): The display name of the chat (e.g., group title,
            user's full name, or channel name). May be None if not applicable.
        type (str | None): The structural category of the chat. Valid values
            are one of the mapped strings at `TelegramChatType`
            May be None if the type is unknown or not present in the export.
        messages (list): A list of message objects contained within this chat.
            **Note:** For public groups and channel exports, this list will
            only contain messages that were sent by the user who requested the
            export, not all messages from the conversation.
    """
    id: int
    name: str | None
    type: str | None
    messages: list


class TelegramMessageWrapper(NamedTuple):
    """An internal wrapper for a Telegram Message object dict."""
    message: dict
    chat_id: int | None
    chat_type: str | None

    @property
    def anchor(self) -> str:
        message_id: str | int | None = self.message.get("id")

        return generate_anchor(message_id, chat_id=self.chat_id, chat_type=self.chat_type)


def generate_anchor(
        message_id: str | int | None, chat_id : int | None, chat_type: str | None
    ) -> str:
    anchor_prefix = "telegram-message-"

    if chat_type is not None and chat_id is not None:
        return f"{anchor_prefix}{chat_type}-{chat_id}-{message_id}"

    return f"{anchor_prefix}{message_id}"


class TelegramChatType(enum.StrEnum):
    """
    Telegram Chat type.

    This is the `type` field in a Telegram chat export Chat object.
    """
    SAVED_MESSAGES      = auto()
    REPLIES             = auto()
    PERSONAL_CHAT       = auto()
    BOT_CHAT            = auto()
    PRIVATE_GROUP       = auto()
    PRIVATE_SUPERGROUP  = auto()
    PUBLIC_SUPERGROUP   = auto()
    PRIVATE_CHANNEL     = auto()
    PUBLIC_CHANNEL      = auto()


class TelegramMessageType(enum.StrEnum):
    """
    Telegram Message type.

    This is the `type` field in a Telegram chat export Message object.
    """

    MESSAGE = auto()
    SERVICE = auto()


class TelegramMessageEntity(enum.StrEnum):
    """
    Telegram MessageEntity types.

    This is the `type` field in a Telegram chat export MessageEntity object.
    """

    UNKNOWN       = auto()
    MENTION       = auto()
    HASHTAG       = auto()
    BOT_COMMAND   = auto()
    LINK          = auto()
    EMAIL         = auto()
    BOLD          = auto()
    ITALIC        = auto()
    CODE          = auto()
    PRE           = auto()
    PLAIN         = auto()
    TEXT_LINK     = auto()
    MENTION_NAME  = auto()
    PHONE         = auto()
    CASHTAG       = auto()
    UNDERLINE     = auto()
    STRIKETHROUGH = auto()
    BLOCKQUOTE    = auto()
    BANK_CARD     = auto()
    SPOILER       = auto()
    CUSTOM_EMOJI  = auto()


class TelegramMessageMediaType(enum.StrEnum):
    """
    Telegram Message media types.

    This is the `media_type` field in a Telegram chat export Message object.
    """

    STICKER       = auto()
    VIDEO_MESSAGE = auto()
    VOICE_MESSAGE = auto()
    ANIMATION     = auto()
    VIDEO_FILE    = auto()
    AUDIO_FILE    = auto()


class TelegramServiceMessageAction(enum.StrEnum):
    """
    Telegram Service message action options.

    This is the `action` field in a Telegram chat export Message object.
    """

    CREATE_GROUP            = auto()
    EDIT_GROUP_TITLE        = auto()
    EDIT_GROUP_PHOTO        = auto()
    DELETE_GROUP_PHOTO      = auto()
    INVITE_MEMBERS          = auto()
    REMOVE_MEMBERS          = auto()
    JOIN_GROUP_BY_LINK      = auto()
    CREATE_CHANNEL          = auto()
    MIGRATE_TO_SUPERGROUP   = auto()
    MIGRATE_FROM_GROUP      = auto()
    PIN_MESSAGE             = auto()
    CLEAR_HISTORY           = auto()
    SCORE_IN_GAME           = auto()
    SEND_PAYMENT            = auto()
    PHONE_CALL              = auto()
    TAKE_SCREENSHOT         = auto()
    ATTACH_MENU_BOT_ALLOWED = auto()
    WEB_APP_BOT_ALLOWED     = auto()
    ALLOW_SENDING_MESSAGES  = auto()
    SEND_PASSPORT_VALUES    = auto()
    JOINED_TELEGRAM         = auto()
    PROXIMITY_REACHED       = auto()
    REQUESTED_PHONE_NUMBER  = auto()
    GROUP_CALL              = auto()
    INVITE_TO_GROUP_CALL    = auto()
    SET_MESSAGES_TTL        = auto()
    GROUP_CALL_SCHEDULED    = auto()
    EDIT_CHAT_THEME         = auto()
    JOIN_GROUP_BY_REQUEST   = auto()
    SEND_WEBVIEW_DATA       = auto()
    SEND_PREMIUM_GIFT       = auto()
    TOPIC_CREATED           = auto()
    TOPIC_EDIT              = auto()
    SUGGEST_PROFILE_PHOTO   = auto()
    REQUESTED_PEER          = auto()
    GIFT_CODE_PRIZE         = auto()
    GIVEAWAY_LAUNCH         = auto()
    SET_CHAT_WALLPAPER      = auto()
    SET_SAME_CHAT_WALLPAPER = auto()
