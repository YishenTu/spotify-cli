# spotify

A command-line interface for Spotify. Control playback, search, manage playlists, switch devices, and more — all from the terminal.

Requires [Spotify Premium](https://www.spotify.com/premium/).

## Setup

### 1. Create a Spotify Developer App

1. Go to [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
2. Create an app
3. Set Redirect URI to `http://127.0.0.1:8888/callback`
4. Note your **Client ID** and **Client Secret**

### 2. Install & authenticate

```bash
# Install dependencies
uv sync

# Authenticate (opens browser)
uv run spotify auth

# Or headless/SSH mode (paste redirect URL manually)
uv run spotify auth --manual
```

Credentials are stored in `~/.config/spotify-cli/config.json`. Tokens auto-refresh — you only need to auth once.

## Usage

### Playback

```bash
spotify play                          # Resume
spotify play "Sexbomb Tom Jones"      # Search + play
spotify pause
spotify next
spotify prev
spotify volume 60
spotify shuffle on|off
spotify repeat off|track|context
```

### Status

```bash
spotify status                        # What's playing
spotify status --json                 # Machine-readable
```

### Search

```bash
spotify search "Tom Jones"
spotify search "Random Access Memories" --type album
spotify search "Jazz Vibes" --type playlist
spotify search "Jamiroquai" --type artist --limit 5
```

### Queue

```bash
spotify queue "September Earth Wind Fire"
```

### Devices

```bash
spotify devices                       # List online devices
spotify device "iPhone"               # Transfer playback
```

### Playlists

```bash
spotify playlist list
spotify playlist create "Swagger & Groove"
spotify playlist add "Swagger & Groove" "Sexbomb" "Baby Come Back" "September"
spotify playlist show "Swagger & Groove"
spotify playlist remove "Swagger & Groove" "Sexbomb"
spotify playlist delete "Swagger & Groove" --yes
```

### Library

```bash
spotify like                          # Like current track
spotify unlike
```

### JSON output

All read commands support `--json` for structured output:

```bash
spotify status --json
spotify devices --json
spotify search "query" --json
spotify playlist list --json
```

## Agent Skill

This CLI ships with an agent skill in `skills/spotify/SKILL.md`, compatible with any agent framework that supports skills (e.g., [OpenClaw](https://openclaw.ai), [Claude Code](https://docs.anthropic.com/en/docs/claude-code), [Codex](https://github.com/openai/codex)). Once installed, an AI agent can control Spotify through natural language.

### Install

Copy the skill into your agent's skills directory:

```bash
# OpenClaw
cp -r skills/spotify ~/.openclaw/skills/spotify

# Or wherever your agent loads skills from
cp -r skills/spotify /path/to/your/skills/spotify
```

The agent calls the CLI via `uv run --directory ~/repos/spotify-cli spotify <command>`. No extra config needed — it reads the same `~/.config/spotify-cli/config.json` credentials.

### What the agent can do

- **Playback** — "play Sexbomb", "pause", "skip", "volume 40", "shuffle on"
- **Search** — "search for Jazz playlists", "find albums by Daft Punk"
- **Playlists** — "create a playlist called Swagger & Groove and add these 10 songs"
- **Devices** — "switch playback to my iPhone"
- **Library** — "like this song"
- **Composite** — "recommend 5 funk songs, create a playlist, and play it on my MacBook"

## Development

```bash
uv sync
uv run pytest
```

## Project structure

```
spotify-cli/
├── src/spotify/
│   ├── cli.py        # Click CLI commands
│   ├── api.py        # Spotify Web API client
│   ├── auth.py       # OAuth flow + token management
│   └── config.py     # Config file helpers
├── tests/
├── skills/spotify/
│   └── SKILL.md      # OpenClaw agent skill
├── pyproject.toml
└── README.md
```

## License

MIT
