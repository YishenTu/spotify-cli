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
spotify seek 90                       # Seek to 90 seconds
spotify seek 1:30                     # Seek to 1 minute 30 seconds (mm:ss)
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
spotify queue "September Earth Wind Fire"     # Add to queue (shorthand)
spotify queue add "September Earth Wind Fire" # Add to queue (explicit)
spotify queue show                            # Show current queue
spotify queue show --limit 5                  # Show top 5 upcoming
spotify queue show --json                     # Machine-readable
```

### History

```bash
spotify history                       # Show last 20 played tracks
spotify history --limit 50            # Show up to 50 tracks
spotify history --json                # Machine-readable
```

### Top

```bash
spotify top                           # Top tracks (~6 months)
spotify top tracks                    # Explicit type
spotify top artists                   # Top artists
spotify top --time-range short        # ~4 weeks
spotify top --time-range medium       # ~6 months (default)
spotify top --time-range long         # All time
spotify top --limit 20                # More results
spotify top --json                    # Machine-readable
```

### Recommendations

```bash
spotify recommend "Kate Bush"         # Recommendations seeded from a track search
spotify recommend "Get Lucky" --limit 20
spotify recommend "Billie Jean" --json
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
spotify playlist create "Chill" --description "Relaxing vibes" --public
spotify playlist add "Swagger & Groove" "Sexbomb" "Baby Come Back" "September"
spotify playlist show "Swagger & Groove"
spotify playlist remove "Swagger & Groove" "Sexbomb"
spotify playlist delete "Swagger & Groove" --yes
spotify playlist rename "Old Name" "New Name"
spotify playlist edit "My Mix" --name "Better Mix" --description "Updated"
spotify playlist reorder "My Mix" 3 1              # Move track at pos 3 to pos 1
spotify playlist play "Swagger & Groove"           # Play entire playlist
spotify playlist dedupe "My Mix"                   # Remove duplicate tracks
spotify playlist dedupe "My Mix" --dry-run         # Preview duplicates without removing
spotify playlist dedupe "My Mix" --json            # Machine-readable duplicate report
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
spotify queue show --json
spotify history --json
spotify top --json
spotify recommend "query" --json
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

## Remote Server

Built-in HTTP server for remote Spotify control — designed for iOS Shortcuts, CarPlay auto-play, or any HTTP client.

### Start

```bash
spotify serve                         # Default: 0.0.0.0:19743
spotify serve --port 8080
```

### Run as a persistent service (macOS)

Create a launchd plist at `~/Library/LaunchAgents/com.spotify-carplay.server.plist` that runs `.venv/bin/python serve.py --port 19743`, then load it:

```bash
launchctl load ~/Library/LaunchAgents/com.spotify-carplay.server.plist
```

### Endpoints

All endpoints except `/health` require `Authorization: Bearer <token>` header. The token is auto-generated on first run and stored in `~/.config/spotify-cli/server.json`.

| Endpoint | Description |
|---|---|
| `GET /health` | Health check (no auth) |
| `GET /play` | Resume last playback, shuffle on |
| `GET /play?playlist=spotify:playlist:XXX` | Play a specific playlist |
| `GET /play?device=iPhone` | Target a device by name |
| `GET /play?shuffle=false` | Play without shuffle |
| `GET /pause` | Pause playback |
| `GET /devices` | List available devices |

The `/play` endpoint includes a retry mechanism (3 attempts, 3s apart) to wait for devices that are still waking up — useful when an iOS Shortcut opens Spotify right before calling the API.

### iOS Shortcut (CarPlay auto-play)

1. **Automation trigger**: CarPlay → Connected → Run Immediately
2. **Action 1**: Open URL → `spotify:`
3. **Action 2**: Get Contents of URL → `http://<tailscale-ip>:19743/play` with header `Authorization: Bearer <token>`

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
│   ├── server.py     # HTTP server for remote control
│   └── config.py     # Config file helpers
├── serve.py          # Standalone entry point for launchd
├── tests/
├── skills/spotify/
│   └── SKILL.md      # OpenClaw agent skill
├── pyproject.toml
└── README.md
```

## License

MIT
