"""Tests for the seek command."""

from click.testing import CliRunner

from spotify.cli import cli


class TestSeek:
    def test_seek_seconds(self, mocker):
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mock = mocker.patch("spotify.api.seek_playback")

        result = CliRunner().invoke(cli, ["seek", "90"])
        assert result.exit_code == 0
        mock.assert_called_once_with(90000)
        assert "1:30" in result.output

    def test_seek_mmss(self, mocker):
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mock = mocker.patch("spotify.api.seek_playback")

        result = CliRunner().invoke(cli, ["seek", "1:30"])
        assert result.exit_code == 0
        mock.assert_called_once_with(90000)
        assert "1:30" in result.output

    def test_seek_invalid(self, mocker):
        mocker.patch("spotify.api.get_valid_token", return_value="tok")

        result = CliRunner().invoke(cli, ["seek", "abc"])
        assert result.exit_code != 0
        assert "Invalid" in result.output

    def test_seek_invalid_mmss(self, mocker):
        mocker.patch("spotify.api.get_valid_token", return_value="tok")

        result = CliRunner().invoke(cli, ["seek", "abc:xyz"])
        assert result.exit_code != 0
        assert "Invalid" in result.output
