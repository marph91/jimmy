from pathlib import Path
import sys
import time
from typing import Optional

from joppy.api import Api
import platformdirs
import requests


API_TOKEN_FILE = (
    Path(platformdirs.user_config_dir("joplin-custom-importer")) / ".joplin_api_token"
)


def request_api_token():
    try:
        response = requests.post("http://localhost:41184/auth", timeout=5)
        if response.status_code == 200:
            auth_token = response.json()["auth_token"]
            print("Please open Joplin and accept the 'grant authorization' dialog.")
        else:
            print(f"Received unexpected HTTP status {response.status_code}.")
            return None
    except requests.exceptions.ConnectionError:
        print(
            "Joplin web clipper is not available. "
            "Please start Joplin and activate the web clipper at "
            "'Tools -> Options -> Web Clipper'."
        )
        return None

    for _ in range(60):
        response = requests.get(
            f"http://localhost:41184/auth/check?auth_token={auth_token}", timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if data["status"] == "accepted":
                print("Authorization granted. Your notes will be imported soon.")
                API_TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
                API_TOKEN_FILE.write_text(data["token"])
                return data["token"]
        time.sleep(1)
    print("Didn't get authorized in 60 seconds. Please try again.")
    return None


def get_api() -> Optional[Api]:
    if API_TOKEN_FILE.is_file():
        # token from config dir
        api_token = API_TOKEN_FILE.read_text()
        api = Api(token=api_token)
        try:
            # check if old token works
            api.get_notes()
        except requests.exceptions.HTTPError:
            # old token doesn't work - request new token
            api_token = request_api_token()
        except requests.exceptions.ConnectionError:
            api_token = None
            print(
                "Joplin web clipper is not available. "
                "Please start Joplin and activate the web clipper at "
                "'Tools -> Options -> Web Clipper'."
            )
    else:
        # no old token - request new token
        api_token = request_api_token()
    if api_token is None:
        sys.exit(1)
    return Api(token=api_token)
