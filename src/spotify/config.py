"""Config file management for spotify CLI (~/.config/spotify-cli/config.json)."""

from spotify.auth import load_config, save_config, CONFIG_DIR, CONFIG_FILE

__all__ = ["load_config", "save_config", "CONFIG_DIR", "CONFIG_FILE"]
