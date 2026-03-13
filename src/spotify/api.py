import requests
from spotify.auth import get_valid_token

BASE_URL = "https://api.spotify.com/v1"


class SpotifyAPIError(Exception):
    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message
        super().__init__(message)


def _headers():
    return {"Authorization": f"Bearer {get_valid_token()}"}


def _handle_response(resp):
    if resp.status_code == 204:
        return None
    if resp.status_code == 404:
        raise SpotifyAPIError(404, "Resource not found.")
    if resp.status_code == 403:
        data = resp.json().get("error", {})
        reason = data.get("reason", "")
        if reason == "PREMIUM_REQUIRED":
            raise SpotifyAPIError(403, "Spotify Premium is required for this action.")
        raise SpotifyAPIError(403, data.get("message", "Forbidden."))
    if not resp.ok:
        try:
            msg = resp.json().get("error", {}).get("message", resp.text)
        except Exception:
            msg = resp.text
        raise SpotifyAPIError(resp.status_code, msg)
    if not resp.text or not resp.text.strip():
        return None
    try:
        return resp.json()
    except Exception:
        return None


# --- Playback ---

def get_current_playback():
    resp = requests.get(f"{BASE_URL}/me/player", headers=_headers())
    if resp.status_code == 204:
        return None
    return _handle_response(resp)


def get_currently_playing():
    resp = requests.get(f"{BASE_URL}/me/player/currently-playing", headers=_headers())
    if resp.status_code == 204:
        return None
    return _handle_response(resp)


def get_devices():
    resp = requests.get(f"{BASE_URL}/me/player/devices", headers=_headers())
    return _handle_response(resp)


def start_playback(device_id=None, uris=None, context_uri=None):
    params = {}
    if device_id:
        params["device_id"] = device_id
    body = {}
    if uris:
        body["uris"] = uris
    if context_uri:
        body["context_uri"] = context_uri
    resp = requests.put(
        f"{BASE_URL}/me/player/play",
        headers=_headers(),
        params=params,
        json=body if body else None,
    )
    return _handle_response(resp)


def pause_playback():
    resp = requests.put(f"{BASE_URL}/me/player/pause", headers=_headers())
    return _handle_response(resp)


def next_track():
    resp = requests.post(f"{BASE_URL}/me/player/next", headers=_headers())
    return _handle_response(resp)


def previous_track():
    resp = requests.post(f"{BASE_URL}/me/player/previous", headers=_headers())
    return _handle_response(resp)


def set_volume(volume_percent):
    resp = requests.put(
        f"{BASE_URL}/me/player/volume",
        headers=_headers(),
        params={"volume_percent": volume_percent},
    )
    return _handle_response(resp)


def set_shuffle(state):
    resp = requests.put(
        f"{BASE_URL}/me/player/shuffle",
        headers=_headers(),
        params={"state": str(state).lower()},
    )
    return _handle_response(resp)


def set_repeat(state):
    resp = requests.put(
        f"{BASE_URL}/me/player/repeat",
        headers=_headers(),
        params={"state": state},
    )
    return _handle_response(resp)


def transfer_playback(device_id):
    resp = requests.put(
        f"{BASE_URL}/me/player",
        headers=_headers(),
        json={"device_ids": [device_id]},
    )
    return _handle_response(resp)


def add_to_queue(uri):
    resp = requests.post(
        f"{BASE_URL}/me/player/queue",
        headers=_headers(),
        params={"uri": uri},
    )
    return _handle_response(resp)


# --- Search ---

def search(query, search_type="track", limit=10):
    resp = requests.get(
        f"{BASE_URL}/search",
        headers=_headers(),
        params={"q": query, "type": search_type, "limit": limit},
    )
    return _handle_response(resp)


# --- Library ---

def save_tracks(track_ids):
    resp = requests.put(
        f"{BASE_URL}/me/tracks",
        headers=_headers(),
        json={"ids": track_ids},
    )
    return _handle_response(resp)


def remove_tracks(track_ids):
    resp = requests.delete(
        f"{BASE_URL}/me/tracks",
        headers=_headers(),
        json={"ids": track_ids},
    )
    return _handle_response(resp)


# --- Playlists ---

def get_current_user_playlists(limit=50):
    playlists = []
    url = f"{BASE_URL}/me/playlists"
    params = {"limit": min(limit, 50)}
    while url and len(playlists) < limit:
        resp = requests.get(url, headers=_headers(), params=params)
        data = _handle_response(resp)
        playlists.extend(data["items"])
        url = data.get("next")
        params = None  # next URL includes params
    return playlists[:limit]


def create_playlist(name, description="", public=False):
    resp = requests.get(f"{BASE_URL}/me", headers=_headers())
    user = _handle_response(resp)
    user_id = user["id"]
    resp = requests.post(
        f"{BASE_URL}/users/{user_id}/playlists",
        headers=_headers(),
        json={"name": name, "description": description, "public": public},
    )
    return _handle_response(resp)


def get_playlist_tracks(playlist_id, limit=50):
    tracks = []
    url = f"{BASE_URL}/playlists/{playlist_id}/tracks"
    params = {"limit": min(limit, 100)}
    while url and len(tracks) < limit:
        resp = requests.get(url, headers=_headers(), params=params)
        data = _handle_response(resp)
        tracks.extend(data["items"])
        url = data.get("next")
        params = None
    return tracks[:limit]


def add_tracks_to_playlist(playlist_id, uris):
    # Spotify limits 100 URIs per request
    for i in range(0, len(uris), 100):
        batch = uris[i:i + 100]
        resp = requests.post(
            f"{BASE_URL}/playlists/{playlist_id}/tracks",
            headers=_headers(),
            json={"uris": batch},
        )
        _handle_response(resp)
    return None


def remove_tracks_from_playlist(playlist_id, uris):
    """Remove tracks from a playlist by URI."""
    tracks = [{"uri": uri} for uri in uris]
    for i in range(0, len(tracks), 100):
        batch = tracks[i:i + 100]
        resp = requests.delete(
            f"{BASE_URL}/playlists/{playlist_id}/tracks",
            headers=_headers(),
            json={"tracks": batch},
        )
        _handle_response(resp)
    return None


def unfollow_playlist(playlist_id):
    """Unfollow (delete) a playlist."""
    resp = requests.delete(
        f"{BASE_URL}/playlists/{playlist_id}/followers",
        headers=_headers(),
    )
    return _handle_response(resp)


def resolve_playlist(name_or_id):
    """Resolve a playlist by exact ID or fuzzy name match."""
    # If it looks like a Spotify ID (22 chars, alphanumeric), try direct lookup
    if len(name_or_id) == 22 and name_or_id.isalnum():
        try:
            resp = requests.get(
                f"{BASE_URL}/playlists/{name_or_id}",
                headers=_headers(),
            )
            return _handle_response(resp)
        except SpotifyAPIError:
            pass

    playlists = get_current_user_playlists(limit=200)
    name_lower = name_or_id.lower()

    # Exact match first
    for p in playlists:
        if p["name"].lower() == name_lower:
            return p

    # Substring match
    for p in playlists:
        if name_lower in p["name"].lower():
            return p

    return None
