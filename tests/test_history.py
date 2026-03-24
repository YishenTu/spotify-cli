"""Tests for the history command."""

import json

from click.testing import CliRunner

from spotify.cli import cli
from tests.conftest import make_track


def _make_history_item(name="Test Track", artist="Test Artist", played_at="2024-01-15T10:00:00Z"):
    return {
        "track": make_track(name, artist),
        "played_at": played_at,
    }


class TestHistory:
    def test_history_default(self, mocker):
        items = [_make_history_item(f"Song {i}", "Artist") for i in range(5)]
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.get_recently_played", return_value={"items": items})

        result = CliRunner().invoke(cli, ["history"])
        assert result.exit_code == 0
        assert "Song 0" in result.output
        assert "Song 4" in result.output
        assert "Artist" in result.output

    def test_history_json(self, mocker):
        items = [_make_history_item("Track A", "Artist X")]
        data = {"items": items}
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.get_recently_played", return_value=data)

        result = CliRunner().invoke(cli, ["history", "--json"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert "items" in parsed
        assert parsed["items"][0]["track"]["name"] == "Track A"

    def test_history_limit(self, mocker):
        items = [_make_history_item(f"Song {i}", "Artist") for i in range(5)]
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mock = mocker.patch("spotify.api.get_recently_played", return_value={"items": items})

        result = CliRunner().invoke(cli, ["history", "--limit", "5"])
        assert result.exit_code == 0
        mock.assert_called_once_with(limit=5)

    def test_history_empty(self, mocker):
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.get_recently_played", return_value={"items": []})

        result = CliRunner().invoke(cli, ["history"])
        assert result.exit_code == 0
        assert "No recently played" in result.output
