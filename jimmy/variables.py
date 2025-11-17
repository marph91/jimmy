"""Contains global variables."""

# current version of jimmy
VERSION = "1.1.10"

# all available formats and their allowed inputs
# use a registry to avoid importing all (including many unneeded) modules
FORMAT_REGISTRY = {
    None: {"accepted_extensions": ["*"], "accept_folder": True},  # default format
    "anki": {"accepted_extensions": [".apkg"], "accept_folder": False},
    "anytype": {"accepted_extensions": [".zip"], "accept_folder": True},
    "bear": {"accepted_extensions": [".bear2bk"], "accept_folder": False},
    "cacher": {"accepted_extensions": [".json"], "accept_folder": False},
    "cherrytree": {"accepted_extensions": [".ctd"], "accept_folder": True},
    "clipto": {"accepted_extensions": [".json"], "accept_folder": False},
    "colornote": {"accepted_extensions": [".backup"], "accept_folder": False},
    "day_one": {"accepted_extensions": [".zip"], "accept_folder": False},
    "diaro": {"accepted_extensions": [".zip"], "accept_folder": False},
    "drafts": {"accepted_extensions": [".draftsexport"], "accept_folder": False},
    "dynalist": {"accepted_extensions": [".zip"], "accept_folder": False},
    "evernote": {"accepted_extensions": [".enex"], "accept_folder": True},
    "facebook": {"accepted_extensions": [".zip"], "accept_folder": False},
    "google_docs": {"accepted_extensions": [".tgz", ".zip"], "accept_folder": False},
    "google_keep": {"accepted_extensions": [".tgz", ".zip"], "accept_folder": False},
    "joplin": {"accepted_extensions": [".jex"], "accept_folder": False},
    "jrnl": {"accepted_extensions": [".json"], "accept_folder": False},
    "nimbus_note": {"accepted_extensions": [".zip"], "accept_folder": True},
    "notion": {"accepted_extensions": [".zip"], "accept_folder": False},
    "obsidian": {"accepted_extensions": None, "accept_folder": True},
    "onenote": {"accepted_extensions": [".zip"], "accept_folder": True},
    "qownnotes": {"accepted_extensions": None, "accept_folder": True},
    "rednotebook": {"accepted_extensions": [".zip"], "accept_folder": True},
    "roam_research": {"accepted_extensions": [".json"], "accept_folder": False},
    "simplenote": {"accepted_extensions": [".zip"], "accept_folder": False},
    "standard_notes": {"accepted_extensions": [".zip"], "accept_folder": False},
    "synology_note_station": {"accepted_extensions": [".nsx"], "accept_folder": False},
    "telegram": {"accepted_extensions": None, "accept_folder": True},
    "textbundle": {"accepted_extensions": [".textbundle", ".textpack"], "accept_folder": True},
    "tiddlywiki": {"accepted_extensions": [".json", ".tid"], "accept_folder": True},
    "tomboy_ng": {"accepted_extensions": [".note"], "accept_folder": True},
    "turtl": {"accepted_extensions": [".json"], "accept_folder": False},
    "upnote": {"accepted_extensions": None, "accept_folder": True},
    "wordpress": {"accepted_extensions": [".xml"], "accept_folder": False},
    "zettelkasten": {"accepted_extensions": [".zkn3"], "accept_folder": False},
    "zim": {"accepted_extensions": None, "accept_folder": True},
    "zoho_notebook": {"accepted_extensions": [".zip"], "accept_folder": False},
}
