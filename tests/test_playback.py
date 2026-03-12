"""Tests for playback commands: status, pause, next, prev, like, unlike, volume, shuffle, repeat."""

from click.testing import CliRunner

from spotify.cli import cli
from tests.conftest import make_track


def _playback_data(is_playing=True, shuffle=False, repeat="off"):
    return {
        "is_playing": is_playing,
        "progress_ms": 65000,
        "shuffle_state": shuffle,
        "repeat_state": repeat,
        "device": {"name": "Speaker", "type": "Speaker"},
        "item": {
            **make_track("Running Up That Hill", "Kate Bush", "Hounds of Love"),
            "duration_ms": 300000,
        },
    }


class TestStatus:
    def test_status_playing(self, mocker):
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.get_current_playback", return_value=_playback_data())

        result = CliRunner().invoke(cli, ["status"])
        assert result.exit_code == 0
        assert "Kate Bush" in result.output
        assert "Running Up That Hill" in result.output
        assert "Speaker" in result.output
        assert "1:05" in result.output  # 65000ms

    def test_status_nothing_playing(self, mocker):
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.get_current_playback", return_value=None)

        result = CliRunner().invoke(cli, ["status"])
        assert result.exit_code != 0
        assert "Nothing is currently playing" in result.output


class TestPause:
    def test_pause(self, mocker):
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mock = mocker.patch("spotify.api.pause_playback")
        result = CliRunner().invoke(cli, ["pause"])
        assert result.exit_code == 0
        assert "Paused" in result.output
        mock.assert_called_once()


class TestNext:
    def test_next(self, mocker):
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mock = mocker.patch("spotify.api.next_track")
        result = CliRunner().invoke(cli, ["next"])
        assert result.exit_code == 0
        mock.assert_called_once()


class TestPrev:
    def test_prev(self, mocker):
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mock = mocker.patch("spotify.api.previous_track")
        result = CliRunner().invoke(cli, ["prev"])
        assert result.exit_code == 0
        mock.assert_called_once()


class TestLike:
    def test_like_current(self, mocker):
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.get_currently_playing", return_value={
            "item": make_track("Song", "Artist"),
        })
        mock_save = mocker.patch("spotify.api.save_tracks")

        result = CliRunner().invoke(cli, ["like"])
        assert result.exit_code == 0
        assert "Liked" in result.output
        mock_save.assert_called_once_with(["abc123"])

    def test_like_nothing_playing(self, mocker):
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.get_currently_playing", return_value=None)

        result = CliRunner().invoke(cli, ["like"])
        assert result.exit_code != 0


class TestUnlike:
    def test_unlike_current(self, mocker):
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.get_currently_playing", return_value={
            "item": make_track("Song", "Artist"),
        })
        mock_remove = mocker.patch("spotify.api.remove_tracks")

        result = CliRunner().invoke(cli, ["unlike"])
        assert result.exit_code == 0
        assert "Unliked" in result.output
        mock_remove.assert_called_once_with(["abc123"])


class TestVolume:
    def test_set_volume(self, mocker):
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mock = mocker.patch("spotify.api.set_volume")

        result = CliRunner().invoke(cli, ["volume", "75"])
        assert result.exit_code == 0
        assert "75%" in result.output
        mock.assert_called_once_with(75)

    def test_volume_out_of_range(self, mocker):
        result = CliRunner().invoke(cli, ["volume", "150"])
        assert result.exit_code != 0


class TestShuffle:
    def test_shuffle_on(self, mocker):
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mock = mocker.patch("spotify.api.set_shuffle")

        result = CliRunner().invoke(cli, ["shuffle", "on"])
        assert result.exit_code == 0
        mock.assert_called_once_with(True)

    def test_shuffle_toggle(self, mocker):
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.get_current_playback", return_value=_playback_data(shuffle=True))
        mock = mocker.patch("spotify.api.set_shuffle")

        result = CliRunner().invoke(cli, ["shuffle"])
        assert result.exit_code == 0
        mock.assert_called_once_with(False)  # toggles off


class TestRepeat:
    def test_repeat_track(self, mocker):
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mock = mocker.patch("spotify.api.set_repeat")

        result = CliRunner().invoke(cli, ["repeat", "track"])
        assert result.exit_code == 0
        mock.assert_called_once_with("track")

    def test_repeat_cycle(self, mocker):
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.get_current_playback", return_value=_playback_data(repeat="off"))
        mock = mocker.patch("spotify.api.set_repeat")

        result = CliRunner().invoke(cli, ["repeat"])
        assert result.exit_code == 0
        mock.assert_called_once_with("context")  # off -> context
