"""Click CLI entry point for spotify."""

import json as json_mod

import click

from spotify import api, auth, server
from spotify.api import SpotifyAPIError


def _handle_api_error(fn):
    """Decorator to catch SpotifyAPIError and print friendly messages."""
    import functools

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except SpotifyAPIError as e:
            raise click.ClickException(e.message)

    return wrapper


def _format_ms(ms):
    """Format milliseconds as m:ss."""
    if ms is None:
        return "0:00"
    s = ms // 1000
    return f"{s // 60}:{s % 60:02d}"


@click.group()
def cli():
    """spotify — Spotify from the command line."""


# --- auth ---

@cli.command()
@click.option("--client-id", default=None, help="Spotify app client ID")
@click.option("--client-secret", default=None, help="Spotify app client secret")
@click.option("--manual", is_flag=True, help="Manual mode: paste redirect URL instead of localhost callback")
def auth_cmd(client_id, client_secret, manual):
    """Authenticate with Spotify."""
    config = auth.load_config()
    if not client_id:
        existing = config.get("client_id", "")
        if existing:
            client_id = click.prompt("Spotify Client ID", default=existing)
        else:
            client_id = click.prompt("Spotify Client ID")
    if not client_secret:
        existing = config.get("client_secret", "")
        if existing:
            client_secret = click.prompt("Spotify Client Secret", default="(saved)", hide_input=True) 
            if client_secret == "(saved)":
                client_secret = existing
        else:
            client_secret = click.prompt("Spotify Client Secret", hide_input=True)
    auth.run_auth_flow(client_id, client_secret, manual=manual)


# Register as 'auth' (can't name the function 'auth' since it shadows the module)
cli.add_command(auth_cmd, "auth")


# --- status ---

@cli.command()
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@_handle_api_error
def status(as_json):
    """Show currently playing track."""
    data = api.get_current_playback()
    if not data or not data.get("item"):
        raise click.ClickException("Nothing is currently playing.")

    item = data["item"]
    artist = ", ".join(a["name"] for a in item.get("artists", []))
    track = item["name"]
    album = item.get("album", {}).get("name", "")
    device = data.get("device", {}).get("name", "Unknown")
    progress = _format_ms(data.get("progress_ms"))
    duration = _format_ms(item.get("duration_ms"))
    is_playing = data.get("is_playing", False)

    if as_json:
        click.echo(json_mod.dumps(data, indent=2))
    else:
        state = "▶" if is_playing else "⏸"
        click.echo(f"{state}  {artist} — {track}")
        click.echo(f"   Album:    {album}")
        click.echo(f"   Device:   {device}")
        click.echo(f"   Progress: {progress} / {duration}")


# --- devices ---

@cli.command()
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@_handle_api_error
def devices(as_json):
    """List available devices."""
    data = api.get_devices()
    device_list = data.get("devices", [])

    if as_json:
        click.echo(json_mod.dumps(device_list, indent=2))
        return

    if not device_list:
        click.echo("No devices found.")
        return

    for d in device_list:
        active = "●" if d.get("is_active") else " "
        vol = d.get("volume_percent", "?")
        click.echo(f"  {active} {d['name']} ({d['type']}) — Volume: {vol}%")


# --- play ---

@cli.command()
@click.argument("query", nargs=-1)
@_handle_api_error
def play(query):
    """Resume playback or search and play a track."""
    if not query:
        api.start_playback()
        click.echo("Resumed playback.")
        return

    query_str = " ".join(query)
    results = api.search(query_str, search_type="track", limit=1)
    tracks = results.get("tracks", {}).get("items", [])
    if not tracks:
        raise click.ClickException(f"No tracks found for '{query_str}'.")

    track = tracks[0]
    artist = ", ".join(a["name"] for a in track["artists"])
    api.start_playback(uris=[track["uri"]])
    click.echo(f"Playing: {artist} — {track['name']} ({track['album']['name']})")


# --- pause ---

@cli.command()
@_handle_api_error
def pause():
    """Pause playback."""
    api.pause_playback()
    click.echo("Paused.")


# --- next ---

@cli.command("next")
@_handle_api_error
def next_cmd():
    """Skip to next track."""
    api.next_track()
    click.echo("Skipped to next track.")


# --- prev ---

@cli.command("prev")
@_handle_api_error
def prev_cmd():
    """Skip to previous track."""
    api.previous_track()
    click.echo("Skipped to previous track.")


# --- search ---

@cli.command()
@click.argument("query", nargs=-1, required=True)
@click.option("--type", "search_type", default="track", type=click.Choice(["track", "album", "artist", "playlist"]))
@click.option("--limit", default=10, type=click.IntRange(1, 50))
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@_handle_api_error
def search(query, search_type, limit, as_json):
    """Search Spotify."""
    query_str = " ".join(query)
    results = api.search(query_str, search_type=search_type, limit=limit)

    if as_json:
        click.echo(json_mod.dumps(results, indent=2))
        return

    key = search_type + "s"
    items = results.get(key, {}).get("items", [])
    if not items:
        click.echo(f"No {search_type}s found for '{query_str}'.")
        return

    for i, item in enumerate(items, 1):
        if search_type == "track":
            artist = ", ".join(a["name"] for a in item["artists"])
            click.echo(f"  {i}. {artist} — {item['name']} ({item['album']['name']})")
        elif search_type == "album":
            artist = ", ".join(a["name"] for a in item["artists"])
            click.echo(f"  {i}. {artist} — {item['name']} ({item.get('release_date', '')})")
        elif search_type == "artist":
            followers = item.get("followers", {}).get("total", 0)
            click.echo(f"  {i}. {item['name']} ({followers:,} followers)")
        elif search_type == "playlist":
            owner = item.get("owner", {}).get("display_name", "")
            total = item.get("tracks", {}).get("total", 0)
            click.echo(f"  {i}. {item['name']} by {owner} ({total} tracks)")


# --- seek ---

@cli.command()
@click.argument("position")
@_handle_api_error
def seek(position):
    """Seek to a position in the current track. Position can be seconds (e.g. 90) or mm:ss (e.g. 1:30)."""
    if ":" in position:
        parts = position.split(":")
        try:
            minutes, seconds = int(parts[0]), int(parts[1])
            position_ms = (minutes * 60 + seconds) * 1000
        except (ValueError, IndexError):
            raise click.ClickException("Invalid position format. Use seconds (90) or mm:ss (1:30).")
    else:
        try:
            position_ms = int(position) * 1000
        except ValueError:
            raise click.ClickException("Invalid position. Use seconds (90) or mm:ss (1:30).")

    api.seek_playback(position_ms)
    total_s = position_ms // 1000
    click.echo(f"Seeked to {total_s // 60}:{total_s % 60:02d}.")


# --- history ---

@cli.command()
@click.option("--limit", default=20, type=click.IntRange(1, 50), help="Number of tracks to show (default 20)")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@_handle_api_error
def history(limit, as_json):
    """Show recently played tracks."""
    data = api.get_recently_played(limit=limit)
    items = data.get("items", [])

    if as_json:
        click.echo(json_mod.dumps(data, indent=2))
        return

    if not items:
        click.echo("No recently played tracks found.")
        return

    for item in items:
        track = item.get("track", {})
        artist = ", ".join(a["name"] for a in track.get("artists", []))
        played_at = item.get("played_at", "")[:19].replace("T", " ")
        click.echo(f"  {played_at}  {artist} — {track.get('name', '?')}")


# --- top ---

@cli.command()
@click.argument("top_type", type=click.Choice(["tracks", "artists"]), default="tracks", required=False)
@click.option("--time-range", type=click.Choice(["short", "medium", "long"]), default="medium",
              help="Time range: short (~4 weeks), medium (~6 months), long (all time). Default: medium.")
@click.option("--limit", default=10, type=click.IntRange(1, 50), help="Number of results (default 10)")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@_handle_api_error
def top(top_type, time_range, limit, as_json):
    """Show your top tracks or artists."""
    time_range_map = {"short": "short_term", "medium": "medium_term", "long": "long_term"}
    data = api.get_top(top_type=top_type, time_range=time_range_map[time_range], limit=limit)
    items = data.get("items", [])

    if as_json:
        click.echo(json_mod.dumps(data, indent=2))
        return

    if not items:
        click.echo(f"No top {top_type} found.")
        return

    range_label = {"short": "~4 weeks", "medium": "~6 months", "long": "all time"}[time_range]
    click.echo(f"Top {top_type} ({range_label}):")
    for i, item in enumerate(items, 1):
        if top_type == "tracks":
            artist = ", ".join(a["name"] for a in item.get("artists", []))
            click.echo(f"  {i:2}. {artist} — {item['name']}")
        else:
            genres = ", ".join(item.get("genres", [])[:2])
            click.echo(f"  {i:2}. {item['name']}" + (f" ({genres})" if genres else ""))


# --- recommend ---

@cli.command()
@click.argument("seed_query", nargs=-1, required=True)
@click.option("--limit", default=10, type=click.IntRange(1, 100), help="Number of recommendations (default 10)")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@_handle_api_error
def recommend(seed_query, limit, as_json):
    """Get track recommendations based on a seed query."""
    query_str = " ".join(seed_query)
    results = api.search(query_str, search_type="track", limit=1)
    seed_tracks = results.get("tracks", {}).get("items", [])
    if not seed_tracks:
        raise click.ClickException(f"No tracks found for seed query '{query_str}'.")

    seed_track = seed_tracks[0]
    seed_artist = ", ".join(a["name"] for a in seed_track["artists"])
    click.echo(f"Seed: {seed_artist} — {seed_track['name']}")

    data = api.get_recommendations(seed_tracks=[seed_track["id"]], limit=limit)
    tracks = data.get("tracks", [])

    if as_json:
        click.echo(json_mod.dumps(data, indent=2))
        return

    if not tracks:
        click.echo("No recommendations found.")
        return

    click.echo(f"\nRecommendations ({len(tracks)}):")
    for i, t in enumerate(tracks, 1):
        artist = ", ".join(a["name"] for a in t.get("artists", []))
        click.echo(f"  {i:2}. {artist} — {t['name']}")


# --- queue ---

class _DefaultCommandGroup(click.Group):
    """A Click group that falls back to a default subcommand when invoked with unknown args."""

    def parse_args(self, ctx, args):
        # If first arg doesn't look like a subcommand, inject "add"
        if args and args[0] not in self.commands and not args[0].startswith("-"):
            args.insert(0, "add")
        return super().parse_args(ctx, args)


@cli.group(cls=_DefaultCommandGroup, invoke_without_command=False)
def queue():
    """Manage the playback queue."""


@queue.command("add")
@click.argument("query", nargs=-1, required=True)
@_handle_api_error
def queue_add(query):
    """Search and add a track to the queue."""
    query_str = " ".join(query)
    results = api.search(query_str, search_type="track", limit=1)
    tracks = results.get("tracks", {}).get("items", [])
    if not tracks:
        raise click.ClickException(f"No tracks found for '{query_str}'.")

    track = tracks[0]
    artist = ", ".join(a["name"] for a in track["artists"])
    api.add_to_queue(track["uri"])
    click.echo(f"Queued: {artist} — {track['name']} ({track['album']['name']})")


@queue.command("show")
@click.option("--limit", default=10, type=click.IntRange(1, 50), help="Number of upcoming tracks to show (default 10)")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@_handle_api_error
def queue_show(limit, as_json):
    """Show the current playback queue."""
    data = api.get_queue()
    if not data:
        click.echo("Queue is empty.")
        return

    if as_json:
        click.echo(json_mod.dumps(data, indent=2))
        return

    current = data.get("currently_playing")
    if current:
        artist = ", ".join(a["name"] for a in current.get("artists", []))
        click.echo(f"Now playing: {artist} — {current['name']}")

    queue_items = data.get("queue", [])[:limit]
    if queue_items:
        click.echo(f"\nUp next ({len(queue_items)} shown):")
        for i, t in enumerate(queue_items, 1):
            artist = ", ".join(a["name"] for a in t.get("artists", []))
            click.echo(f"  {i}. {artist} — {t['name']}")
    else:
        click.echo("Queue is empty.")


# --- device ---

@cli.command()
@click.argument("name_or_id")
@_handle_api_error
def device(name_or_id):
    """Transfer playback to a device (by name or ID)."""
    data = api.get_devices()
    device_list = data.get("devices", [])

    # Try exact ID match
    for d in device_list:
        if d["id"] == name_or_id:
            api.transfer_playback(d["id"])
            click.echo(f"Transferred playback to {d['name']}.")
            return

    # Fuzzy name match
    name_lower = name_or_id.lower()
    for d in device_list:
        if name_lower in d["name"].lower():
            api.transfer_playback(d["id"])
            click.echo(f"Transferred playback to {d['name']}.")
            return

    raise click.ClickException(f"No device matching '{name_or_id}' found.")


# --- playlist group ---

@cli.group()
def playlist():
    """Manage playlists."""


@playlist.command("list")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@_handle_api_error
def playlist_list(as_json):
    """List your playlists."""
    playlists = api.get_current_user_playlists()

    if as_json:
        click.echo(json_mod.dumps(playlists, indent=2))
        return

    if not playlists:
        click.echo("No playlists found.")
        return

    for i, p in enumerate(playlists, 1):
        total = p.get("tracks", {}).get("total", 0)
        click.echo(f"  {i}. {p['name']} ({total} tracks)")


@playlist.command("create")
@click.argument("name")
@click.option("--description", default="", help="Playlist description")
@click.option("--public", is_flag=True, help="Make playlist public")
@_handle_api_error
def playlist_create(name, description, public):
    """Create a new playlist."""
    result = api.create_playlist(name, description=description, public=public)
    click.echo(f"Created playlist: {result['name']}")


@playlist.command("add")
@click.argument("playlist_name_or_id")
@click.argument("tracks", nargs=-1, required=True)
@_handle_api_error
def playlist_add(playlist_name_or_id, tracks):
    """Add tracks to a playlist. Each argument is a search query."""
    pl = api.resolve_playlist(playlist_name_or_id)
    if not pl:
        raise click.ClickException(f"Playlist '{playlist_name_or_id}' not found.")

    uris = []
    for query in tracks:
        if query.startswith("spotify:track:"):
            uris.append(query)
            click.echo(f"  + URI: {query}")
            continue
        results = api.search(query, search_type="track", limit=1)
        items = results.get("tracks", {}).get("items", [])
        if not items:
            click.echo(f"  No results for '{query}', skipping.")
            continue
        t = items[0]
        artist = ", ".join(a["name"] for a in t["artists"])
        click.echo(f"  + {artist} — {t['name']} ({t['album']['name']})")
        uris.append(t["uri"])

    if uris:
        api.add_tracks_to_playlist(pl["id"], uris)
        click.echo(f"Added {len(uris)} track(s) to '{pl['name']}'.")
    else:
        click.echo("No tracks to add.")


@playlist.command("show")
@click.argument("playlist_name_or_id")
@click.option("--limit", default=50, type=click.IntRange(1, 200))
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@_handle_api_error
def playlist_show(playlist_name_or_id, limit, as_json):
    """Show tracks in a playlist."""
    pl = api.resolve_playlist(playlist_name_or_id)
    if not pl:
        raise click.ClickException(f"Playlist '{playlist_name_or_id}' not found.")

    tracks = api.get_playlist_tracks(pl["id"], limit=limit)

    if as_json:
        click.echo(json_mod.dumps(tracks, indent=2))
        return

    click.echo(f"{pl['name']} ({len(tracks)} tracks shown)")
    for i, item in enumerate(tracks, 1):
        t = item.get("track")
        if not t:
            continue
        artist = ", ".join(a["name"] for a in t.get("artists", []))
        click.echo(f"  {i}. {artist} — {t['name']}")


@playlist.command("remove")
@click.argument("playlist_name_or_id")
@click.argument("tracks", nargs=-1, required=True)
@_handle_api_error
def playlist_remove(playlist_name_or_id, tracks):
    """Remove tracks from a playlist. Each argument is a search query or URI."""
    pl = api.resolve_playlist(playlist_name_or_id)
    if not pl:
        raise click.ClickException(f"Playlist '{playlist_name_or_id}' not found.")

    uris = []
    for query in tracks:
        if query.startswith("spotify:track:"):
            uris.append(query)
            continue
        results = api.search(query, search_type="track", limit=1)
        items = results.get("tracks", {}).get("items", [])
        if not items:
            click.echo(f"  No results for '{query}', skipping.")
            continue
        t = items[0]
        artist = ", ".join(a["name"] for a in t["artists"])
        click.echo(f"  - {artist} — {t['name']}")
        uris.append(t["uri"])

    if uris:
        api.remove_tracks_from_playlist(pl["id"], uris)
        click.echo(f"Removed {len(uris)} track(s) from '{pl['name']}'.")
    else:
        click.echo("No tracks to remove.")


@playlist.command("delete")
@click.argument("playlist_name_or_id")
@click.confirmation_option(prompt="Are you sure you want to delete this playlist?")
@_handle_api_error
def playlist_delete(playlist_name_or_id):
    """Delete (unfollow) a playlist."""
    pl = api.resolve_playlist(playlist_name_or_id)
    if not pl:
        raise click.ClickException(f"Playlist '{playlist_name_or_id}' not found.")

    api.unfollow_playlist(pl["id"])
    click.echo(f"Deleted playlist: {pl['name']}")


@playlist.command("rename")
@click.argument("old_name")
@click.argument("new_name")
@_handle_api_error
def playlist_rename(old_name, new_name):
    """Rename a playlist."""
    pl = api.resolve_playlist(old_name)
    if not pl:
        raise click.ClickException(f"Playlist '{old_name}' not found.")

    api.update_playlist(pl["id"], name=new_name)
    click.echo(f"Renamed '{pl['name']}' → '{new_name}'.")


@playlist.command("edit")
@click.argument("playlist_name_or_id")
@click.option("--name", "new_name", default=None, help="New playlist name")
@click.option("--description", "new_description", default=None, help="New playlist description")
@_handle_api_error
def playlist_edit(playlist_name_or_id, new_name, new_description):
    """Edit playlist metadata (name and/or description). At least one option required."""
    if new_name is None and new_description is None:
        raise click.UsageError("At least one of --name or --description must be provided.")

    pl = api.resolve_playlist(playlist_name_or_id)
    if not pl:
        raise click.ClickException(f"Playlist '{playlist_name_or_id}' not found.")

    api.update_playlist(pl["id"], name=new_name, description=new_description)
    changes = []
    if new_name:
        changes.append(f"name → '{new_name}'")
    if new_description is not None:
        changes.append(f"description → '{new_description}'")
    click.echo(f"Updated '{pl['name']}': {', '.join(changes)}.")


@playlist.command("reorder")
@click.argument("playlist_name_or_id")
@click.argument("from_pos", type=int, metavar="FROM")
@click.argument("to_pos", type=int, metavar="TO")
@_handle_api_error
def playlist_reorder(playlist_name_or_id, from_pos, to_pos):
    """Reorder tracks in a playlist (1-indexed positions).

    Move the track at FROM position to before the TO position.
    """
    pl = api.resolve_playlist(playlist_name_or_id)
    if not pl:
        raise click.ClickException(f"Playlist '{playlist_name_or_id}' not found.")

    # Convert 1-indexed to 0-indexed for the API
    range_start = from_pos - 1
    insert_before = to_pos - 1 if to_pos > from_pos else to_pos - 1

    api.reorder_playlist_tracks(pl["id"], range_start=range_start, insert_before=insert_before)
    click.echo(f"Moved track from position {from_pos} to {to_pos} in '{pl['name']}'.")


@playlist.command("play")
@click.argument("playlist_name_or_id")
@_handle_api_error
def playlist_play(playlist_name_or_id):
    """Play a playlist."""
    pl = api.resolve_playlist(playlist_name_or_id)
    if not pl:
        raise click.ClickException(f"Playlist '{playlist_name_or_id}' not found.")

    context_uri = pl.get("uri") or f"spotify:playlist:{pl['id']}"
    api.start_playback(context_uri=context_uri)
    total = pl.get("tracks", {}).get("total", "?")
    click.echo(f"Playing playlist: {pl['name']} ({total} tracks).")


@playlist.command("dedupe")
@click.argument("playlist_name_or_id")
@click.option("--dry-run", is_flag=True, help="Show duplicates without removing them")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@_handle_api_error
def playlist_dedupe(playlist_name_or_id, dry_run, as_json):
    """Remove duplicate tracks from a playlist."""
    pl = api.resolve_playlist(playlist_name_or_id)
    if not pl:
        raise click.ClickException(f"Playlist '{playlist_name_or_id}' not found.")

    tracks = api.get_playlist_tracks(pl["id"], limit=200)
    seen_ids = {}
    duplicates = []

    for i, item in enumerate(tracks):
        t = item.get("track")
        if not t or not t.get("id"):
            continue
        tid = t["id"]
        if tid in seen_ids:
            artist = ", ".join(a["name"] for a in t.get("artists", []))
            duplicates.append({
                "position": i,
                "id": tid,
                "name": t["name"],
                "artist": artist,
                "uri": t["uri"],
                "first_seen_at": seen_ids[tid],
            })
        else:
            seen_ids[tid] = i

    if as_json:
        click.echo(json_mod.dumps({"playlist": pl["name"], "duplicates": duplicates, "dry_run": dry_run}, indent=2))
        return

    if not duplicates:
        click.echo(f"No duplicates found in '{pl['name']}'.")
        return

    click.echo(f"Found {len(duplicates)} duplicate(s) in '{pl['name']}':")
    for d in duplicates:
        click.echo(f"  pos {d['position'] + 1}: {d['artist']} — {d['name']} (first at pos {d['first_seen_at'] + 1})")

    if dry_run:
        click.echo("\n[dry-run] No tracks removed.")
        return

    # Remove duplicates (remove by URI — removes all occurrences, then re-add the kept ones)
    # Use positional removal via snapshot approach: remove each duplicate URI occurrence
    dup_uris = list({d["uri"] for d in duplicates})
    api.remove_tracks_from_playlist(pl["id"], dup_uris)
    click.echo(f"\nRemoved {len(dup_uris)} duplicate track(s) from '{pl['name']}'.")


# --- like / unlike ---

@cli.command()
@_handle_api_error
def like():
    """Like the currently playing track."""
    data = api.get_currently_playing()
    if not data or not data.get("item"):
        raise click.ClickException("Nothing is currently playing.")

    track = data["item"]
    artist = ", ".join(a["name"] for a in track["artists"])
    api.save_tracks([track["id"]])
    click.echo(f"Liked: {artist} — {track['name']}")


@cli.command()
@_handle_api_error
def unlike():
    """Remove the currently playing track from liked songs."""
    data = api.get_currently_playing()
    if not data or not data.get("item"):
        raise click.ClickException("Nothing is currently playing.")

    track = data["item"]
    artist = ", ".join(a["name"] for a in track["artists"])
    api.remove_tracks([track["id"]])
    click.echo(f"Unliked: {artist} — {track['name']}")


# --- volume ---

@cli.command()
@click.argument("level", type=click.IntRange(0, 100))
@_handle_api_error
def volume(level):
    """Set playback volume (0-100)."""
    api.set_volume(level)
    click.echo(f"Volume set to {level}%.")


# --- shuffle ---

@cli.command()
@click.argument("state", type=click.Choice(["on", "off"]), required=False, default=None)
@_handle_api_error
def shuffle(state):
    """Toggle or set shuffle mode."""
    if state is None:
        # Toggle based on current state
        data = api.get_current_playback()
        if not data:
            raise click.ClickException("No active playback.")
        current = data.get("shuffle_state", False)
        state = "off" if current else "on"

    api.set_shuffle(state == "on")
    click.echo(f"Shuffle: {state}.")


# --- serve ---

@cli.command()
@click.option("--host", default="0.0.0.0", help="Bind address")
@click.option("--port", default=server.DEFAULT_PORT, type=int, help="Port")
def serve(host, port):
    """Start HTTP server for remote control (e.g. CarPlay)."""
    server.run_server(host=host, port=port)


# --- repeat ---

@cli.command()
@click.argument("state", type=click.Choice(["off", "track", "context"]), required=False, default=None)
@_handle_api_error
def repeat(state):
    """Set repeat mode (off, track, context)."""
    if state is None:
        # Cycle: off -> context -> track -> off
        data = api.get_current_playback()
        if not data:
            raise click.ClickException("No active playback.")
        current = data.get("repeat_state", "off")
        cycle = {"off": "context", "context": "track", "track": "off"}
        state = cycle.get(current, "off")

    api.set_repeat(state)
    click.echo(f"Repeat: {state}.")
