"""Shared fixtures for spotify tests."""

import pytest


@pytest.fixture
def mock_config(tmp_path, mocker):
    """Patch config to use a temp directory."""
    config_file = tmp_path / "config.json"
    mocker.patch("spotify.auth.CONFIG_DIR", tmp_path)
    mocker.patch("spotify.auth.CONFIG_FILE", config_file)
    return config_file


def make_track(name="Test Track", artist="Test Artist", album="Test Album",
               uri="spotify:track:abc123", track_id="abc123"):
    """Helper to build a mock track object."""
    return {
        "id": track_id,
        "name": name,
        "uri": uri,
        "artists": [{"name": artist}],
        "album": {"name": album},
        "duration_ms": 210000,
    }


def make_device(name="My Speaker", device_type="Speaker", active=True,
                volume=50, device_id="device123"):
    return {
        "id": device_id,
        "name": name,
        "type": device_type,
        "is_active": active,
        "volume_percent": volume,
    }


def make_playlist(name="My Playlist", playlist_id="pl123", total=10):
    return {
        "id": playlist_id,
        "name": name,
        "tracks": {"total": total},
        "owner": {"display_name": "testuser"},
    }
