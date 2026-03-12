"""Tests for device listing and selection."""

from click.testing import CliRunner

from spotify.cli import cli
from tests.conftest import make_device


class TestDevicesCommand:
    def test_list_devices(self, mocker):
        devices = [
            make_device("Living Room", "Speaker", True, 80, "d1"),
            make_device("Phone", "Smartphone", False, 50, "d2"),
        ]
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.get_devices", return_value={"devices": devices})

        result = CliRunner().invoke(cli, ["devices"])
        assert result.exit_code == 0
        assert "Living Room" in result.output
        assert "Phone" in result.output
        assert "●" in result.output  # active indicator

    def test_no_devices(self, mocker):
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.get_devices", return_value={"devices": []})

        result = CliRunner().invoke(cli, ["devices"])
        assert "No devices found" in result.output


class TestDeviceCommand:
    def test_transfer_by_name(self, mocker):
        devices = [make_device("Kitchen", device_id="k1")]
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.get_devices", return_value={"devices": devices})
        mock_transfer = mocker.patch("spotify.api.transfer_playback")

        result = CliRunner().invoke(cli, ["device", "kitchen"])
        assert result.exit_code == 0
        assert "Kitchen" in result.output
        mock_transfer.assert_called_once_with("k1")

    def test_transfer_by_id(self, mocker):
        devices = [make_device("Desk", device_id="desk_id_123")]
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.get_devices", return_value={"devices": devices})
        mock_transfer = mocker.patch("spotify.api.transfer_playback")

        result = CliRunner().invoke(cli, ["device", "desk_id_123"])
        assert result.exit_code == 0
        mock_transfer.assert_called_once_with("desk_id_123")

    def test_device_not_found(self, mocker):
        mocker.patch("spotify.api.get_valid_token", return_value="tok")
        mocker.patch("spotify.api.get_devices", return_value={"devices": []})

        result = CliRunner().invoke(cli, ["device", "ghost"])
        assert result.exit_code != 0
        assert "No device matching" in result.output
