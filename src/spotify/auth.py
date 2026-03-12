import json
import time
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlencode, urlparse, parse_qs

import requests

CONFIG_DIR = Path.home() / ".config" / "spotify-cli"
CONFIG_FILE = CONFIG_DIR / "config.json"

SCOPES = " ".join([
    "user-read-playback-state",
    "user-modify-playback-state",
    "user-read-currently-playing",
    "playlist-read-private",
    "playlist-modify-public",
    "playlist-modify-private",
    "user-library-modify",
    "user-library-read",
])

REDIRECT_URI = "http://127.0.0.1:8888/callback"
AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"


def load_config():
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}


def save_config(config):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2))
    try:
        CONFIG_FILE.chmod(0o600)
    except OSError:
        pass


def get_auth_url(client_id):
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
    }
    return f"{AUTH_URL}?{urlencode(params)}"


class _CallbackHandler(BaseHTTPRequestHandler):
    auth_code = None

    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        if "code" in query:
            _CallbackHandler.auth_code = query["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>Authorization successful! You can close this tab.</h1>")
        else:
            error = query.get("error", ["unknown"])[0]
            self.send_response(400)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(f"<h1>Authorization failed: {error}</h1>".encode())

    def log_message(self, format, *args):
        pass  # suppress server logs


def wait_for_callback():
    server = HTTPServer(("127.0.0.1", 8888), _CallbackHandler)
    _CallbackHandler.auth_code = None
    server.handle_request()
    server.server_close()
    return _CallbackHandler.auth_code


def exchange_code(client_id, client_secret, code):
    resp = requests.post(TOKEN_URL, data={
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": client_id,
        "client_secret": client_secret,
    })
    resp.raise_for_status()
    return resp.json()


def refresh_access_token(client_id, client_secret, refresh_token):
    resp = requests.post(TOKEN_URL, data={
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
    })
    resp.raise_for_status()
    return resp.json()


def get_valid_token():
    config = load_config()
    for key in ("client_id", "client_secret", "refresh_token"):
        if key not in config:
            raise SystemExit("Not authenticated. Run 'spotify auth' first.")

    token_expiry = config.get("token_expiry", 0)
    if time.time() < token_expiry - 60:
        return config["access_token"]

    data = refresh_access_token(
        config["client_id"], config["client_secret"], config["refresh_token"]
    )
    config["access_token"] = data["access_token"]
    config["token_expiry"] = time.time() + data["expires_in"]
    if "refresh_token" in data:
        config["refresh_token"] = data["refresh_token"]
    save_config(config)
    return config["access_token"]


def run_auth_flow(client_id, client_secret, manual=False):
    config = load_config()
    config["client_id"] = client_id
    config["client_secret"] = client_secret
    save_config(config)

    url = get_auth_url(client_id)

    if manual:
        print(f"Open this URL in any browser:\n\n{url}\n")
        print("After authorizing, you'll be redirected to a localhost URL.")
        print("Copy the FULL redirect URL from the address bar and paste it here.\n")
        redirect_url = input("Paste redirect URL: ").strip()
        query = parse_qs(urlparse(redirect_url).query)
        code = query.get("code", [None])[0]
        if not code:
            raise SystemExit("Authorization failed: no code found in URL.")
    else:
        print(f"Opening browser for authorization...\n{url}")
        webbrowser.open(url)
        print("Waiting for callback on localhost:8888...")
        code = wait_for_callback()
        if not code:
            raise SystemExit("Authorization failed: no code received.")

    data = exchange_code(client_id, client_secret, code)
    config["access_token"] = data["access_token"]
    config["refresh_token"] = data["refresh_token"]
    config["token_expiry"] = time.time() + data["expires_in"]
    save_config(config)
    print("Authentication successful! Credentials saved.")
