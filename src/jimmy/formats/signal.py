"""Convert Signal chats to the intermediate format."""

from pathlib import Path

import sigexport.create
import sigexport.data
import sigexport.files
import sigexport.models

from jimmy import common, converter, intermediate_format as imf
import jimmy.md_lib.conversations
import jimmy.md_lib.links


class Converter(converter.BaseConverter):
    def __init__(self, config: common.Config):
        super().__init__(config)
        self.password = config.password
        self.resource_folder = common.get_temp_folder()

    @common.catch_all_exceptions()
    def convert_note(self, title, messages: list[sigexport.models.Message]):
        self.logger.debug(f'Converting chat "{title}"')
        note_imf = imf.Note(title, source_application=self.format)

        md_conversation = jimmy.md_lib.conversations.Conversation()
        for message in messages:
            if note_imf.created is None:
                # created date is the date of the first message
                note_imf.created = message.date

            md_message = jimmy.md_lib.conversations.Message(
                message.sender,
                message.body,
                prefix=message.date.strftime("%Y-%m-%d %H:%M:%S"),
                quote=message.quote,
            )

            for resource in message.attachments:
                resource_path = self.resource_folder / title / resource.path
                resource_link = jimmy.md_lib.links.make_link(
                    resource.name, str(resource_path), is_image=common.is_image(Path(resource.path))
                )
                md_message.attachment_links.append(resource_link)

                if resource_path.exists():
                    note_imf.resources.append(imf.Resource(resource_path, resource_link))
                else:
                    # self.logger.debug(f"File '{resource_path}' doesn't exist. Ignoring.")
                    pass  # silently skip old files to don't pollute the log

            md_conversation.messages.append(md_message)

            # update the updated time each message to get the timestamp
            # of the last message at the end
            note_imf.updated = message.date
        note_imf.body = md_conversation.to_md()

        if not note_imf.body:
            self.logger.debug("Skipping empty chat.")
            return

        self.root_notebook.child_notes.append(note_imf)

    def convert(self, file_or_folder: Path):
        source_folder = file_or_folder.expanduser().resolve()

        cursor = sigexport.data.get_signal_database(
            source_folder,
            password=self.password,
            key=None,
        )

        convos, contacts, _ = sigexport.data.fetch_data(
            source_folder,
            cursor,
            chats="",  # all chats
            include_empty=False,
            include_disappearing=True,
        )

        sigexport.files.copy_attachments(
            source_folder, self.resource_folder, convos, contacts, cursor
        )

        chat_dict = sigexport.create.create_chats(convos, contacts)

        for key, messages in chat_dict.items():
            name = contacts[key].name or common.unique_title()  # some contact names are None
            self.convert_note(name.strip(), messages)
