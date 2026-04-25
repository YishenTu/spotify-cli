---
name: spotify
description: Control Spotify playback, search, manage playlists, switch devices, and manage library via the spotify CLI. Use when the user wants to play/pause/skip music, search for songs/albums/artists, create or edit playlists, check what's playing, switch playback between devices, adjust volume, manage liked songs, seek within a track, view history, browse top tracks/artists, or get recommendations. Triggers on music-related requests like "play something", "create a playlist", "what's playing", "skip", "switch to iPhone", "add this to my playlist", "seek to 1:30", "show my history", "what are my top tracks", "recommend songs like this".
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
spotify seek 90                       # Seek to 90 seconds
spotify seek 1:30                     # Seek to 1 minute 30 seconds (mm:ss)
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
spotify queue "September Earth Wind Fire"     # Add to queue (shorthand)
spotify queue add "September Earth Wind Fire" # Add to queue (explicit)
spotify queue show                            # Show current queue + up next
spotify queue show --limit 5                  # Show top 5 upcoming tracks
spotify queue show --json                     # Machine-readable
```

### History

```bash
spotify history                       # Show last 20 recently played tracks
spotify history --limit 50            # Show up to 50 tracks
spotify history --json                # Machine-readable
```

### Top

```bash
spotify top                           # Top tracks (~6 months, default)
spotify top tracks                    # Explicit: top tracks
spotify top artists                   # Top artists
spotify top --time-range short        # ~4 weeks
spotify top --time-range medium       # ~6 months (default)
spotify top --time-range long         # All time
spotify top --limit 20                # More results (default 10)
spotify top --json                    # Machine-readable
```

### Recommendations

```bash
spotify recommend "Kate Bush"             # Seed from a track search, get 10 recs
spotify recommend "Get Lucky" --limit 20  # More recommendations
spotify recommend "Billie Jean" --json    # Machine-readable
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
spotify playlist delete "Swagger & Groove" --yes           # Delete (unfollow) playlist
spotify playlist rename "Old Name" "New Name"              # Rename a playlist
spotify playlist edit "My Mix" --name "Better Mix"         # Edit name
spotify playlist edit "My Mix" --description "New desc"    # Edit description
spotify playlist edit "My Mix" --name "N" --description "D" # Edit both
spotify playlist reorder "My Mix" 3 1                      # Move track pos 3 to pos 1 (1-indexed)
spotify playlist play "Swagger & Groove"                   # Play entire playlist
spotify playlist dedupe "My Mix"                           # Remove duplicate tracks
spotify playlist dedupe "My Mix" --dry-run                 # Preview without removing
spotify playlist dedupe "My Mix" --json                    # Machine-readable duplicate report
```

### Library

```bash
spotify like                          # Like currently playing track
spotify unlike                        # Unlike currently playing track
```

## Agent Patterns

### Seek to a specific position

```bash
spotify seek 1:30                     # Jump to 1 minute 30 seconds
spotify seek 90                       # Jump to 90 seconds (same as above)
```

### Show listening history

```bash
spotify history --limit 10            # Last 10 tracks played
spotify history --json                # Full JSON for further processing
```

### Discover top content

```bash
spotify top artists --time-range short     # What I've been playing lately
spotify top tracks --time-range long       # My all-time favorites
```

### Get recommendations and queue them

```bash
spotify recommend "Kate Bush Running Up That Hill" --limit 5   # Seed from track
spotify queue add "Track A"
spotify queue add "Track B"
```

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

### Clean up a playlist

```bash
spotify playlist dedupe "My Mix" --dry-run   # Preview duplicates
spotify playlist dedupe "My Mix"             # Remove them
```

## Notes

- All read commands support `--json` for structured output.
- Playlist matching is fuzzy by name; use exact Spotify ID if ambiguous.
- `spotify play <query>` searches tracks by default; for albums use `spotify search` first.
- If no active device: prompt user to open Spotify on any device, then `spotify devices` to verify.
- Auth tokens auto-refresh; no manual renewal needed.
- `spotify queue <query>` (without subcommand) adds to queue for backward compatibility.
- `spotify top` defaults to tracks, medium time range (~6 months), limit 10.
- `spotify recommend` finds a seed track by search, then fetches Spotify recommendations from it.
- `spotify playlist reorder` uses 1-indexed positions: `reorder "My Mix" FROM TO` moves the track at position FROM to before position TO.

## Errors & Gotchas

- **`Error: Insufficient client scope`** — the stored OAuth token is missing a required scope. The fix is **not just re-auth**: (a) verify the scope is declared in `src/spotify/auth.py` (`SCOPES` list), add it if missing; (b) **revoke the app at https://www.spotify.com/account/apps/** so Spotify can't silently reuse prior consent; (c) run `spotify auth` again. Skipping (b) is a common trap — without `show_dialog=true` in auth params, Spotify reuses the old grant and the new scopes never get attached.
- **`Error: Resource not found` right after switching device** — happens when `play` runs immediately after `spotify device "<name>"`, especially for Bluetooth speakers. The device hasn't fully registered as active yet. Wait ~2 seconds (or re-check `spotify devices` until the target shows the active marker `●`), then retry.
- **`Error: Nothing is currently playing.`** — `status`, `like`, `unlike`, `seek`, `queue add` (and friends) all need an active playback session. Start playback in any Spotify client first.
- **No active device** — `play` and friends will fail. Run `spotify devices`; if empty, open Spotify somewhere.
- **Auth subcommand is just `spotify auth`** — there is no `auth status`. To inspect token state, look at `~/.config/spotify-cli/config.json` (contains `access_token`, `refresh_token`, `token_expiry`).
- **Premium required** for any playback control; search and read commands work on free accounts.
