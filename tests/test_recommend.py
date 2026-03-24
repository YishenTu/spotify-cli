"""Tests for the recommend command."""

import json

from click.testing import CliRunner

from spotify.cli import cli
from tests.conftest import make_track


class TestRecommend:
    def test_recommend_default(self, mocker):
        seed_track = make_track("Eye of the Tiger", "Survivor")
        rec_tracks = [make_track(f"Rec Track {i}", f"Artist {i}") for i in range(5)]
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.search", return_value={"tracks": {"items": [seed_track]}})
        mocker.patch("spotify.api.get_recommendations", return_value={"tracks": rec_tracks})

        result = CliRunner().invoke(cli, ["recommend", "eye of the tiger"])
        assert result.exit_code == 0
        assert "Seed:" in result.output
        assert "Eye of the Tiger" in result.output
        assert "Rec Track 0" in result.output
        assert "Recommendations" in result.output

    def test_recommend_json(self, mocker):
        seed_track = make_track("Come Together", "Beatles")
        rec_tracks = [make_track("Hey Jude", "Beatles")]
        data = {"tracks": rec_tracks}
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.search", return_value={"tracks": {"items": [seed_track]}})
        mocker.patch("spotify.api.get_recommendations", return_value=data)

        result = CliRunner().invoke(cli, ["recommend", "come together", "--json"])
        assert result.exit_code == 0
        # Output starts with "Seed: ..." line then JSON
        assert "Come Together" in result.output
        # Extract only the JSON portion (starts with '{')
        json_start = result.output.index("{")
        parsed = json.loads(result.output[json_start:])
        assert "tracks" in parsed
        assert parsed["tracks"][0]["name"] == "Hey Jude"

    def test_recommend_no_results(self, mocker):
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.search", return_value={"tracks": {"items": []}})

        result = CliRunner().invoke(cli, ["recommend", "xyzgibberishxyz"])
        assert result.exit_code != 0
        assert "No tracks found" in result.output

    def test_recommend_calls_api_with_seed_track_id(self, mocker):
        seed_track = make_track("Song", "Artist", track_id="seed_id_123")
        rec_tracks = [make_track("Rec 1", "Artist")]
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.search", return_value={"tracks": {"items": [seed_track]}})
        mock_rec = mocker.patch("spotify.api.get_recommendations", return_value={"tracks": rec_tracks})

        CliRunner().invoke(cli, ["recommend", "song", "--limit", "5"])
        mock_rec.assert_called_once_with(seed_tracks=["seed_id_123"], limit=5)
