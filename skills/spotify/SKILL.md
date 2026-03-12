---
name: spotify
description: Control Spotify playback, search, manage playlists, switch devices, and manage library via the spotify CLI. Use when the user wants to play/pause/skip music, search for songs/albums/artists, create or edit playlists, check what's playing, switch playback between devices, adjust volume, or manage liked songs. Triggers on music-related requests like "play something", "create a playlist", "what's playing", "skip", "switch to iPhone", "add this to my playlist".
---

# Spotify (spotify CLI)

Control Spotify via `spotify`. Requires Spotify Premium.

- **CLI location:** `~/repos/spotify-cli/` (source in `src/spotify/`)
- **Run:** `uv run --directory ~/repos/spotify-cli spotify <command>`
- **Config:** `~/.config/spotify-cli/config.json`

## Setup (one-time)

```bash
uv run --directory ~/repos/spotify-cli spotify auth
```

Opens browser → user authorizes → tokens stored automatically.

## Commands

### Playback

```bash
spotify play                          # Resume playback
spotify play "Sexbomb Tom Jones"      # Search + play
spotify pause
spotify next
spotify prev
spotify volume 60
spotify shuffle on                    # on|off
spotify repeat track                  # off|track|context
```

### Status

```bash
spotify status                        # Now playing: artist, track, album, device, progress
spotify status --json                 # Machine-readable
```

### Search

```bash
spotify search "Tom Jones"                    # Default: tracks
spotify search "Random Access Memories" --type album
spotify search "Jazz Vibes" --type playlist
spotify search "Jamiroquai" --type artist --limit 5
spotify search "funk classics" --json         # Machine-readable
```

### Queue

```bash
spotify queue "September Earth Wind Fire"     # Add to queue
```

### Devices

```bash
spotify devices                       # List online devices
spotify device "iPhone"               # Transfer playback to device
spotify device "MacBook Air"
```

### Playlists

```bash
spotify playlist list                                      # All user playlists
spotify playlist create "Swagger & Groove"                 # Create playlist
spotify playlist create "Chill" --description "Relaxing"   # With description
spotify playlist add "Swagger & Groove" "Sexbomb" "Baby Come Back" "September"
                                                        # Search + add multiple tracks
spotify playlist add "Swagger & Groove" spotify:track:xxx  # Add by URI
spotify playlist show "Swagger & Groove"                   # List tracks
spotify playlist show "Swagger & Groove" --limit 20
spotify playlist remove "Swagger & Groove" "Sexbomb"       # Remove track by search
spotify playlist remove "Swagger & Groove" spotify:track:x # Remove by URI
spotify playlist delete "Swagger & Groove" --yes            # Delete (unfollow) playlist
```

### Library

```bash
spotify like                          # Like currently playing track
spotify unlike                        # Unlike currently playing track
```

## Agent Patterns

### Recommend + play on specific device

```bash
spotify devices                              # Check which devices are online
spotify device "iPhone"                      # Switch to target device
spotify play "Canned Heat Jamiroquai"        # Search + play
```

### Build a playlist from recommendations

```bash
spotify playlist create "Swagger & Groove"
spotify playlist add "Swagger & Groove" "Sexbomb Tom Jones" "Baby Come Back Player" "September Earth Wind Fire" "Get Lucky Daft Punk" "Uptown Funk Mark Ronson"
```

### Add currently playing to a playlist

```bash
spotify status --json                        # Get current track URI
spotify playlist add "My Favorites" spotify:track:<uri_from_status>
```

## Notes

- All read commands support `--json` for structured output.
- Playlist matching is fuzzy by name; use exact Spotify ID if ambiguous.
- `spotify play <query>` searches tracks by default; for albums use `spotify search` first.
- If no active device: prompt user to open Spotify on any device, then `spotify devices` to verify.
- Auth tokens auto-refresh; no manual renewal needed.
