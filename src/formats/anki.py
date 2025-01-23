"""Convert Anki cards to the intermediate format."""

from pathlib import Path
import json
import re
import sqlite3

import common
import converter
import intermediate_format as imf


IMAGE_RE = re.compile(r"(<img src=\"(.*?)\"(?:>| >| \/>))")
SOUND_RE = re.compile(r"(\[sound:(.*?)\])")


def get_images(body: str) -> list[tuple[str, str]]:
    """
    >>> get_images('<img src="awake-55ab4bc5f5.jpg">')
    [('<img src="awake-55ab4bc5f5.jpg">', 'awake-55ab4bc5f5.jpg')]
    >>> get_images('<img src="prepositions_14.jpg" />')
    [('<img src="prepositions_14.jpg" />', 'prepositions_14.jpg')]
    """
    return IMAGE_RE.findall(body)


def get_sounds(body: str) -> list[tuple[str, str]]:
    """
    >>> get_sounds("[sound:rec1430907056.mp3]")
    [('[sound:rec1430907056.mp3]', 'rec1430907056.mp3')]
    >>> get_sounds("[ k ]<br />[sound:8c6e1b3ba2f.mp3]")
    [('[sound:8c6e1b3ba2f.mp3]', '8c6e1b3ba2f.mp3')]
    """
    return SOUND_RE.findall(body)


# TODO
# pylint: disable=too-many-locals,too-many-arguments,too-many-positional-arguments
class Converter(converter.BaseConverter):
    accepted_extensions = [".apkg"]

    @common.catch_all_exceptions
    def convert_note(self, note_index, db_row, models, media_dict, note_deck_id_map):
        # TODO: Anki doesn't have note names. Find a robust note name.
        # The index is a bit better readeable than the original_id.
        title = f"note_{note_index:010}"
        self.logger.debug(f'Converting note "{title}"')

        (created, original_id, model_id, updated, tags, data) = db_row
        model = models[str(model_id)]
        template_replacements = dict(
            zip([f["name"] for f in model["flds"]], data.split("\x1f"))
        )

        # TODO: Templates are too complex for pandoc conversion.
        # Just take the replacements for now.
        # def replace(templ, replacements):
        #     for key, value in replacements.items():
        #         templ = templ.replace(f"{{{{{key}}}}}", value + " ")
        #     return templ

        # for template in model["tmpls"]:
        #     front = replace(template["qfmt"], template_replacements)
        #     template_replacements["FrontSide"] = front

        #     # treat the backside as complete note
        #     back = (
        #         model["css"]
        #         + "\n\n"
        #         + replace(template["afmt"], template_replacements)
        #     )
        #     body = markdown_lib.common.markup_to_markdown(back)
        body_md = "\n".join(
            [f"- {key}: {value}" for key, value in template_replacements.items()]
        )
        # cleanup
        body_md = (
            body_md.replace("<br>\n", "\n")
            .replace("&nbsp;", " ")
            .replace("<div>", "")
            .replace("</div>", "")
        )

        # find images, sounds and other attachments
        resources = []
        for text, filename_note in get_images(body_md) + get_sounds(body_md):
            resources.append(
                imf.Resource(
                    self.root_path / media_dict[filename_note],
                    text,
                    filename_note,
                )
            )

        note_imf = imf.Note(
            title,
            body_md,
            original_id=str(original_id),
            created=created,
            updated=updated,
            resources=resources,
            tags=[imf.Tag(t) for t in tags.strip().split(" ") if t],
        )

        found_parent_notebook = False
        parent_deck_id = note_deck_id_map.get(str(created))
        for notebook in self.root_notebook.child_notebooks:
            if notebook.original_id == parent_deck_id:
                notebook.child_notes.append(note_imf)
                found_parent_notebook = True
                break
        if not found_parent_notebook:
            self.root_notebook.child_notes.append(note_imf)

    def convert(self, file_or_folder: Path):
        if (self.root_path / "collection.anki21").is_file():
            db_file = self.root_path / "collection.anki21"
        elif (self.root_path / "collection.anki2").is_file():
            db_file = self.root_path / "collection.anki2"
        else:
            self.logger.error("Couldn't find note database.")
            return

        media_dict = json.loads((self.root_path / "media").read_text(encoding="utf-8"))
        # switch keys and values, because we need the names in the notes later
        media_dict = {v: k for k, v in media_dict.items()}

        conn = sqlite3.connect(db_file)
        cur = conn.cursor()

        # collection
        # https://github.com/ankidroid/Anki-Android/wiki/Database-Structure#collection
        collection = list(cur.execute("select * from col"))[0]
        if collection[4] != 11:
            self.logger.warning(
                f"Only tested with version 11. Got version {collection[4]}"
            )

        # models
        # https://github.com/ankidroid/Anki-Android/wiki/Database-Structure#models-jsonobjects
        models = json.loads(collection[9])

        # decks
        # https://github.com/ankidroid/Anki-Android/wiki/Database-Structure#decks-jsonobjects
        decks = json.loads(collection[10])
        # TODO: nested decks
        for deck_id, deck in decks.items():
            self.root_notebook.child_notebooks.append(
                imf.Notebook(deck["name"], original_id=str(deck_id))
            )

        # cards
        # https://github.com/ankidroid/Anki-Android/wiki/Database-Structure#cards
        note_deck_id_map = {}
        for note_id, deck_id in cur.execute("select nid, did from cards"):
            note_deck_id_map[str(note_id)] = str(deck_id)

        # notes
        # https://github.com/ankidroid/Anki-Android/wiki/Database-Structure#notes
        for note_index, db_row in enumerate(
            cur.execute("select id, guid, mid, mod, tags, flds from notes")
        ):
            self.convert_note(note_index, db_row, models, media_dict, note_deck_id_map)

        # Don't export empty notebooks
        self.remove_empty_notebooks()
