"""Helper functions for connecting to the Joplin data API."""

from pathlib import Path
import time

from joppy.client_api import ClientApi
import platformdirs
import requests


API_TOKEN_FILE = Path(platformdirs.user_config_dir("jimmy")) / ".joplin_api_token"


def request_api_token(info_function, error_function):
    try:
        response = requests.post("http://localhost:41184/auth", timeout=5)
        if response.status_code == 200:
            auth_token = response.json()["auth_token"]
            info_function(
                "Please open Joplin and accept the 'grant authorization' dialog."
            )
        else:
            error_function(f"Received unexpected HTTP status {response.status_code}.")
            return None
    except requests.exceptions.ConnectionError:
        error_function(
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
            match data["status"]:
                case "accepted":
                    info_function(
                        "Authorization granted. Your notes will be imported soon."
                    )
                    API_TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
                    API_TOKEN_FILE.write_text(data["token"])
                    return data["token"]
                case "rejected":
                    error_function("Got rejected. Please try again.")
                    return None
        time.sleep(1)
    error_function("Didn't get authorized in 60 seconds. Please try again.")
    return None


def get_api(info_function, error_function) -> ClientApi | None:
    if API_TOKEN_FILE.is_file():
        # token from config dir
        api_token: str | None = API_TOKEN_FILE.read_text(encoding="utf-8")
        assert api_token is not None
        api = ClientApi(token=api_token)
        try:
            # check if old token works
            api.get_notes()
        except requests.exceptions.HTTPError:
            # old token doesn't work - request new token
            api_token = request_api_token(info_function, error_function)
        except requests.exceptions.ConnectionError:
            api_token = None
            error_function(
                "Joplin web clipper is not available. "
                "Please start Joplin and activate the web clipper at "
                "'Tools -> Options -> Web Clipper'."
            )
    else:
        # no old token - request new token
        api_token = request_api_token(info_function, error_function)
    if api_token is None:
        return None
    return ClientApi(token=api_token)
