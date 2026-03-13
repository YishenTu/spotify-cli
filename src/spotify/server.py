"""HTTP server for remote Spotify control (e.g. CarPlay auto-play).

Endpoints:
  GET /play              Resume last playback (shuffle on by default)
  GET /play?playlist=URI Play a specific playlist
  GET /play?device=NAME  Target a specific device by name
  GET /play?shuffle=false  Disable shuffle
  GET /play?retries=N&delay=S  Retry N times with S second delays
  GET /pause             Pause playback
  GET /devices           List available devices
  GET /health            Health check (no auth required)

All endpoints except /health require: Authorization: Bearer <token>
"""

import json
import logging
import secrets
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from spotify import api

SERVER_CONFIG = Path.home() / ".config" / "spotify-cli" / "server.json"
DEFAULT_PORT = 19743

log = logging.getLogger("spotify.server")


# --- Server config (bearer token) ---

def _load_server_config():
    if SERVER_CONFIG.exists():
        return json.loads(SERVER_CONFIG.read_text())
    return {}


def _save_server_config(config):
    SERVER_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    SERVER_CONFIG.write_text(json.dumps(config, indent=2))
    try:
        SERVER_CONFIG.chmod(0o600)
    except OSError:
        pass


def get_or_create_token():
    sc = _load_server_config()
    if "token" not in sc:
        sc["token"] = secrets.token_urlsafe(32)
        _save_server_config(sc)
        log.info("Generated new bearer token")
    return sc["token"]


# --- Helpers using existing spotify api/auth modules ---

def _find_device(name=None):
    """Find a device by name. Returns (device_id, devices_list)."""
    data = api.get_devices()
    devices = data.get("devices", [])
    if not devices:
        return None, devices
    if name:
        name_lower = name.lower()
        for d in devices:
            if name_lower in d["name"].lower():
                return d["id"], devices
    for d in devices:
        if d["is_active"]:
            return d["id"], devices
    return devices[0]["id"], devices


def _start_playback(device_id=None, context_uri=None, shuffle=True, device_active=False):
    """Start/resume playback with optional shuffle."""
    # Only transfer if targeting a non-active device
    if device_id and not device_active:
        try:
            api.transfer_playback(device_id)
            time.sleep(0.5)
        except api.SpotifyAPIError:
            pass  # best-effort

    # Play
    try:
        api.start_playback(device_id=device_id, context_uri=context_uri)
    except api.SpotifyAPIError as e:
        # 403 "Restriction violated" usually means already playing — treat as success
        if e.status_code == 403 and "restriction" in e.message.lower():
            pass
        else:
            return False, e.status_code, e.message

    # Shuffle
    try:
        api.set_shuffle(shuffle)
    except api.SpotifyAPIError:
        pass  # non-critical

    return True, 200, ""


# --- HTTP Handler ---

class _Handler(BaseHTTPRequestHandler):
    bearer_token = None

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        params = parse_qs(parsed.query)

        if path == "/health":
            self._json(200, {"status": "ok"})
            return

        token = self.headers.get("Authorization", "")
        if token != f"Bearer {self.bearer_token}":
            self._json(401, {"error": "unauthorized"})
            return

        try:
            if path == "/play":
                self._handle_play(params)
            elif path == "/pause":
                try:
                    api.pause_playback()
                    self._json(200, {"action": "pause", "ok": True})
                except api.SpotifyAPIError as e:
                    self._json(502, {"action": "pause", "ok": False, "error": e.message})
            elif path == "/devices":
                data = api.get_devices()
                devices = data.get("devices", [])
                self._json(200, {"devices": [
                    {"name": d["name"], "type": d["type"], "id": d["id"], "active": d["is_active"]}
                    for d in devices
                ]})
            else:
                self._json(404, {"error": "not found"})
        except Exception as e:
            log.exception("Request failed")
            self._json(500, {"error": str(e)})

    def _handle_play(self, params):
        device_name = params.get("device", [None])[0]
        playlist = params.get("playlist", [None])[0]
        shuffle = params.get("shuffle", ["true"])[0].lower() != "false"
        try:
            max_retries = max(1, min(10, int(params.get("retries", ["3"])[0])))
        except (ValueError, TypeError):
            max_retries = 3
        try:
            retry_delay = max(1, min(10, int(params.get("delay", ["3"])[0])))
        except (ValueError, TypeError):
            retry_delay = 3

        device_id, devices = None, []
        for attempt in range(max_retries):
            device_id, devices = _find_device(device_name)
            if device_id:
                break
            if attempt < max_retries - 1:
                log.info(f"No device found, retry {attempt+1}/{max_retries} in {retry_delay}s...")
                time.sleep(retry_delay)

        if not device_id:
            self._json(503, {
                "action": "play", "ok": False,
                "error": "no_device",
                "message": f"No active device found after {max_retries} attempts",
            })
            return

        # Check if the found device is already active
        device_active = any(d.get("is_active") and d["id"] == device_id for d in devices)

        ok, status_code, detail = _start_playback(
            device_id=device_id, context_uri=playlist, shuffle=shuffle,
            device_active=device_active,
        )
        resp = {
            "action": "play", "ok": ok,
            "device_id": device_id, "playlist": playlist, "shuffle": shuffle,
            "devices_available": [d["name"] for d in devices],
        }
        if not ok:
            resp["detail"] = detail
        self._json(200 if ok else 502, resp)

    def _json(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        log.info(fmt % args)


class _ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True


def run_server(host="0.0.0.0", port=DEFAULT_PORT):
    """Start the HTTP server."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    token = get_or_create_token()
    log.info(f"Bearer token: {token[:8]}...{token[-4:]}")
    log.info(f"Listening on {host}:{port}")

    _Handler.bearer_token = token
    server = _ReusableHTTPServer((host, port), _Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Shutting down")
        server.server_close()
