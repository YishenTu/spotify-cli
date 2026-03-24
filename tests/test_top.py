"""Tests for the top command."""

import json

from click.testing import CliRunner

from spotify.cli import cli
from tests.conftest import make_track


def _make_artist(name="Test Artist", genres=None):
    return {
        "id": "artist123",
        "name": name,
        "genres": genres or ["pop", "rock"],
        "followers": {"total": 1000000},
    }


class TestTop:
    def test_top_tracks_default(self, mocker):
        tracks = [make_track(f"Track {i}", f"Artist {i}") for i in range(5)]
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mock = mocker.patch("spotify.api.get_top", return_value={"items": tracks})

        result = CliRunner().invoke(cli, ["top"])
        assert result.exit_code == 0
        mock.assert_called_once_with(top_type="tracks", time_range="medium_term", limit=10)
        assert "Track 0" in result.output
        assert "Artist 0" in result.output

    def test_top_artists(self, mocker):
        artists = [_make_artist(f"Artist {i}") for i in range(3)]
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mock = mocker.patch("spotify.api.get_top", return_value={"items": artists})

        result = CliRunner().invoke(cli, ["top", "artists"])
        assert result.exit_code == 0
        mock.assert_called_once_with(top_type="artists", time_range="medium_term", limit=10)
        assert "Artist 0" in result.output

    def test_top_json(self, mocker):
        tracks = [make_track("Song A", "Band X")]
        data = {"items": tracks}
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.get_top", return_value=data)

        result = CliRunner().invoke(cli, ["top", "--json"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert "items" in parsed
        assert parsed["items"][0]["name"] == "Song A"

    def test_top_time_range_short(self, mocker):
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mock = mocker.patch("spotify.api.get_top", return_value={"items": []})

        result = CliRunner().invoke(cli, ["top", "--time-range", "short"])
        assert result.exit_code == 0
        mock.assert_called_once_with(top_type="tracks", time_range="short_term", limit=10)

    def test_top_time_range_long(self, mocker):
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mock = mocker.patch("spotify.api.get_top", return_value={"items": []})

        result = CliRunner().invoke(cli, ["top", "--time-range", "long"])
        assert result.exit_code == 0
        mock.assert_called_once_with(top_type="tracks", time_range="long_term", limit=10)

    def test_top_time_range_medium(self, mocker):
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mock = mocker.patch("spotify.api.get_top", return_value={"items": []})

        result = CliRunner().invoke(cli, ["top", "--time-range", "medium"])
        assert result.exit_code == 0
        mock.assert_called_once_with(top_type="tracks", time_range="medium_term", limit=10)

    def test_top_empty(self, mocker):
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.get_top", return_value={"items": []})

        result = CliRunner().invoke(cli, ["top"])
        assert result.exit_code == 0
        assert "No top tracks" in result.output
