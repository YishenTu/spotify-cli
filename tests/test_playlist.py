"""Tests for playlist operations."""

from click.testing import CliRunner

from spotify.cli import cli
from tests.conftest import make_playlist, make_track


class TestPlaylistList:
    def test_list_playlists(self, mocker):
        playlists = [make_playlist(f"Playlist {i}") for i in range(3)]
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.get_current_user_playlists", return_value=playlists)

        result = CliRunner().invoke(cli, ["playlist", "list"])
        assert result.exit_code == 0
        assert "Playlist 0" in result.output
        assert "Playlist 2" in result.output

    def test_list_empty(self, mocker):
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.get_current_user_playlists", return_value=[])

        result = CliRunner().invoke(cli, ["playlist", "list"])
        assert "No playlists found" in result.output


class TestPlaylistCreate:
    def test_create_playlist(self, mocker):
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.create_playlist", return_value={"name": "My New PL"})

        result = CliRunner().invoke(cli, ["playlist", "create", "My New PL"])
        assert result.exit_code == 0
        assert "My New PL" in result.output

    def test_create_playlist_with_options(self, mocker):
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mock_create = mocker.patch("spotify.api.create_playlist", return_value={"name": "Public PL"})

        result = CliRunner().invoke(cli, [
            "playlist", "create", "Public PL",
            "--description", "A great playlist",
            "--public",
        ])
        assert result.exit_code == 0
        mock_create.assert_called_once_with(
            "Public PL", description="A great playlist", public=True,
        )


class TestPlaylistAdd:
    def test_add_tracks(self, mocker):
        pl = make_playlist("Workout")
        track = make_track("Eye of the Tiger", "Survivor")
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.resolve_playlist", return_value=pl)
        mocker.patch("spotify.api.search", return_value={"tracks": {"items": [track]}})
        mock_add = mocker.patch("spotify.api.add_tracks_to_playlist")

        result = CliRunner().invoke(cli, ["playlist", "add", "Workout", "eye of the tiger"])
        assert result.exit_code == 0
        assert "Survivor" in result.output
        assert "Added 1 track(s)" in result.output
        mock_add.assert_called_once_with("pl123", ["spotify:track:abc123"])

    def test_add_playlist_not_found(self, mocker):
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.resolve_playlist", return_value=None)

        result = CliRunner().invoke(cli, ["playlist", "add", "Nonexistent", "song"])
        assert result.exit_code != 0
        assert "not found" in result.output

    def test_add_no_matching_tracks(self, mocker):
        pl = make_playlist("Empty")
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.resolve_playlist", return_value=pl)
        mocker.patch("spotify.api.search", return_value={"tracks": {"items": []}})

        result = CliRunner().invoke(cli, ["playlist", "add", "Empty", "gibberish"])
        assert "No tracks to add" in result.output


class TestPlaylistShow:
    def test_show_playlist(self, mocker):
        pl = make_playlist("Chill")
        tracks = [{"track": make_track(f"Song {i}", f"Artist {i}")} for i in range(3)]
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.resolve_playlist", return_value=pl)
        mocker.patch("spotify.api.get_playlist_tracks", return_value=tracks)

        result = CliRunner().invoke(cli, ["playlist", "show", "Chill"])
        assert result.exit_code == 0
        assert "Chill" in result.output
        assert "Song 0" in result.output
        assert "Artist 2" in result.output

    def test_show_not_found(self, mocker):
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.resolve_playlist", return_value=None)

        result = CliRunner().invoke(cli, ["playlist", "show", "nope"])
        assert result.exit_code != 0
        assert "not found" in result.output


class TestResolvePlaylist:
    def test_resolve_by_exact_name(self, mocker):
        from spotify.api import resolve_playlist
        playlists = [make_playlist("My Mix"), make_playlist("Other")]
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.get_current_user_playlists", return_value=playlists)

        result = resolve_playlist("My Mix")
        assert result["name"] == "My Mix"

    def test_resolve_by_substring(self, mocker):
        from spotify.api import resolve_playlist
        playlists = [make_playlist("Daily Mix 1"), make_playlist("Workout Jams")]
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.get_current_user_playlists", return_value=playlists)

        result = resolve_playlist("workout")
        assert result["name"] == "Workout Jams"

    def test_resolve_not_found(self, mocker):
        from spotify.api import resolve_playlist
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.get_current_user_playlists", return_value=[])

        result = resolve_playlist("nonexistent")
        assert result is None
