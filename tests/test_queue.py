"""Tests for the queue command group."""

import json

from click.testing import CliRunner

from spotify.cli import cli
from tests.conftest import make_track


def _make_queue_data(current=None, upcoming=None):
    if current is None:
        current = make_track("Now Playing", "Current Artist")
    if upcoming is None:
        upcoming = [make_track(f"Queued {i}", f"Artist {i}") for i in range(3)]
    return {
        "currently_playing": current,
        "queue": upcoming,
    }


class TestQueueAdd:
    def test_queue_add(self, mocker):
        track = make_track("September", "Earth Wind & Fire")
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.search", return_value={"tracks": {"items": [track]}})
        mock_add = mocker.patch("spotify.api.add_to_queue")

        result = CliRunner().invoke(cli, ["queue", "add", "september earth wind fire"])
        assert result.exit_code == 0
        assert "Queued" in result.output
        assert "September" in result.output
        mock_add.assert_called_once_with("spotify:track:abc123")

    def test_queue_add_no_results(self, mocker):
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.search", return_value={"tracks": {"items": []}})

        result = CliRunner().invoke(cli, ["queue", "add", "xyzgibberish"])
        assert result.exit_code != 0
        assert "No tracks found" in result.output


class TestQueueShow:
    def test_queue_show(self, mocker):
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.get_queue", return_value=_make_queue_data())

        result = CliRunner().invoke(cli, ["queue", "show"])
        assert result.exit_code == 0
        assert "Now Playing" in result.output
        assert "Queued 0" in result.output

    def test_queue_show_json(self, mocker):
        data = _make_queue_data()
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.get_queue", return_value=data)

        result = CliRunner().invoke(cli, ["queue", "show", "--json"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert "currently_playing" in parsed
        assert "queue" in parsed

    def test_queue_show_empty(self, mocker):
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.get_queue", return_value=None)

        result = CliRunner().invoke(cli, ["queue", "show"])
        assert result.exit_code == 0
        assert "empty" in result.output.lower()

    def test_queue_show_no_queue_items(self, mocker):
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.get_queue", return_value={
            "currently_playing": make_track("Now Playing", "Artist"),
            "queue": [],
        })

        result = CliRunner().invoke(cli, ["queue", "show"])
        assert result.exit_code == 0
        assert "Queue is empty" in result.output


class TestQueueBackwardCompat:
    def test_queue_backward_compat(self, mocker):
        """queue <query> without subcommand should add to queue (backward compat)."""
        track = make_track("Get Lucky", "Daft Punk")
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.search", return_value={"tracks": {"items": [track]}})
        mock_add = mocker.patch("spotify.api.add_to_queue")

        result = CliRunner().invoke(cli, ["queue", "get lucky daft punk"])
        assert result.exit_code == 0
        assert "Queued" in result.output
        mock_add.assert_called_once_with("spotify:track:abc123")
