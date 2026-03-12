"""Tests for auth token management."""

import json
import time

import pytest

from spotify import auth


class TestLoadSaveConfig:
    def test_load_empty(self, mock_config):
        assert auth.load_config() == {}

    def test_save_and_load(self, mock_config):
        auth.save_config({"client_id": "abc", "access_token": "tok"})
        config = auth.load_config()
        assert config["client_id"] == "abc"
        assert config["access_token"] == "tok"


class TestGetValidToken:
    def test_missing_keys_raises(self, mock_config):
        auth.save_config({})
        with pytest.raises(SystemExit, match="Not authenticated"):
            auth.get_valid_token()

    def test_returns_cached_token_if_not_expired(self, mock_config):
        auth.save_config({
            "client_id": "id",
            "client_secret": "secret",
            "refresh_token": "rt",
            "access_token": "cached_token",
            "token_expiry": time.time() + 3600,
        })
        assert auth.get_valid_token() == "cached_token"

    def test_refreshes_expired_token(self, mock_config, mocker):
        auth.save_config({
            "client_id": "id",
            "client_secret": "secret",
            "refresh_token": "rt",
            "access_token": "old_token",
            "token_expiry": time.time() - 100,  # expired
        })

        mock_refresh = mocker.patch("spotify.auth.refresh_access_token", return_value={
            "access_token": "new_token",
            "expires_in": 3600,
        })

        token = auth.get_valid_token()
        assert token == "new_token"
        mock_refresh.assert_called_once_with("id", "secret", "rt")

        # Verify saved to disk
        config = auth.load_config()
        assert config["access_token"] == "new_token"

    def test_refresh_updates_refresh_token_if_provided(self, mock_config, mocker):
        auth.save_config({
            "client_id": "id",
            "client_secret": "secret",
            "refresh_token": "old_rt",
            "access_token": "old",
            "token_expiry": 0,
        })

        mocker.patch("spotify.auth.refresh_access_token", return_value={
            "access_token": "new",
            "expires_in": 3600,
            "refresh_token": "new_rt",
        })

        auth.get_valid_token()
        config = auth.load_config()
        assert config["refresh_token"] == "new_rt"


class TestGetAuthUrl:
    def test_includes_all_params(self):
        url = auth.get_auth_url("my_client_id")
        assert "client_id=my_client_id" in url
        assert "response_type=code" in url
        assert "redirect_uri=" in url
        assert "scope=" in url


class TestExchangeCode:
    def test_exchange_calls_token_endpoint(self, mocker):
        mock_resp = mocker.Mock()
        mock_resp.raise_for_status = mocker.Mock()
        mock_resp.json.return_value = {
            "access_token": "at",
            "refresh_token": "rt",
            "expires_in": 3600,
        }
        mock_post = mocker.patch("spotify.auth.requests.post", return_value=mock_resp)

        result = auth.exchange_code("cid", "csecret", "code123")
        assert result["access_token"] == "at"
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert call_kwargs[1]["data"]["code"] == "code123"
