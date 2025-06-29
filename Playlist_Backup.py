"""Backs up all playlists and their track IDs to a JSON file for recovery or analysis.
"""
import json
from Playlist_Tools import get_existing_playlists, get_playlist_track_ids

BACKUP_FILE = "playlists_backup.json"

def backup_all_playlists():
    """Back up all playlists and their track IDs to a JSON file."""
    print("Backing up all playlists to", BACKUP_FILE)
    playlists = get_existing_playlists()
    backup = {}
    for name, pid in playlists.items():
        print(f"Backing up '{name}'...")
        track_ids = list(get_playlist_track_ids(pid))
        backup[name] = {"id": pid, "track_ids": track_ids}
    with open(BACKUP_FILE, "w", encoding="utf-8") as f:
        json.dump(backup, f, indent=2)
    print(f"Backup complete: {len(backup)} playlists saved.")

if __name__ == "__main__":
    backup_all_playlists() 