"""Tests for search functionality via CLI."""

import json

from click.testing import CliRunner

from spotify.cli import cli
from tests.conftest import make_track


class TestSearchCommand:
    def test_search_tracks(self, mocker):
        tracks = [make_track(f"Song {i}", f"Artist {i}") for i in range(3)]
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.search", return_value={
            "tracks": {"items": tracks},
        })

        result = CliRunner().invoke(cli, ["search", "test query"])
        assert result.exit_code == 0
        assert "Artist 0" in result.output
        assert "Song 2" in result.output

    def test_search_no_results(self, mocker):
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.search", return_value={"tracks": {"items": []}})

        result = CliRunner().invoke(cli, ["search", "nothing"])
        assert "No tracks found" in result.output

    def test_search_json_output(self, mocker):
        tracks = [make_track()]
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.search", return_value={"tracks": {"items": tracks}})

        result = CliRunner().invoke(cli, ["search", "--json", "test"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert "tracks" in parsed

    def test_search_albums(self, mocker):
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.search", return_value={
            "albums": {"items": [{
                "name": "Album X",
                "artists": [{"name": "Band"}],
                "release_date": "2023",
            }]},
        })

        result = CliRunner().invoke(cli, ["search", "--type", "album", "test"])
        assert "Album X" in result.output
        assert "Band" in result.output

    def test_search_artists(self, mocker):
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.search", return_value={
            "artists": {"items": [{
                "name": "Cool Band",
                "followers": {"total": 50000},
            }]},
        })

        result = CliRunner().invoke(cli, ["search", "--type", "artist", "cool"])
        assert "Cool Band" in result.output
        assert "50,000" in result.output

    def test_search_playlists(self, mocker):
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.search", return_value={
            "playlists": {"items": [{
                "name": "Chill Vibes",
                "owner": {"display_name": "dj_cool"},
                "tracks": {"total": 42},
            }]},
        })

        result = CliRunner().invoke(cli, ["search", "--type", "playlist", "chill"])
        assert "Chill Vibes" in result.output
        assert "dj_cool" in result.output


class TestPlayCommand:
    def test_play_search_and_play(self, mocker):
        track = make_track("Bohemian Rhapsody", "Queen", "Night at the Opera")
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.search", return_value={"tracks": {"items": [track]}})
        mock_play = mocker.patch("spotify.api.start_playback")

        result = CliRunner().invoke(cli, ["play", "bohemian", "rhapsody"])
        assert result.exit_code == 0
        assert "Queen" in result.output
        assert "Bohemian Rhapsody" in result.output
        mock_play.assert_called_once_with(uris=["spotify:track:abc123"])

    def test_play_resume(self, mocker):
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mock_play = mocker.patch("spotify.api.start_playback")

        result = CliRunner().invoke(cli, ["play"])
        assert result.exit_code == 0
        assert "Resumed" in result.output
        mock_play.assert_called_once_with()

    def test_play_no_results(self, mocker):
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.search", return_value={"tracks": {"items": []}})

        result = CliRunner().invoke(cli, ["play", "nonexistent"])
        assert result.exit_code != 0
        assert "No tracks found" in result.output


class TestQueueCommand:
    def test_queue_track(self, mocker):
        track = make_track("Song", "Artist", "Album")
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.search", return_value={"tracks": {"items": [track]}})
        mock_queue = mocker.patch("spotify.api.add_to_queue")

        result = CliRunner().invoke(cli, ["queue", "song"])
        assert result.exit_code == 0
        assert "Queued" in result.output
        mock_queue.assert_called_once_with("spotify:track:abc123")
