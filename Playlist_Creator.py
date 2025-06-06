import spotipy
from spotipy.oauth2 import SpotifyOAuth
from collections import defaultdict
import time
import json
import os
from typing import Dict, List, Set, Any
from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, PLAYLIST_ID
from Playlist_Tools import (
    get_playlist_tracks,
    get_track_genres,
    normalize_genre,
    get_existing_playlists,
    get_playlist_track_ids,
    sp
)

# Initialize Spotify client
sp: spotipy.Spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope='playlist-modify-public playlist-modify-private user-library-read'
))

# Cache file path
CACHE_FILE = "track_genre_cache.json"

def load_track_cache() -> Dict[str, List[str]]:
    """Load the track genre cache from file if it exists."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Cache file corrupted, starting with empty cache")
            return {}
    return {}

def save_track_cache(cache: Dict[str, List[str]]) -> None:
    """Save the track genre cache to file."""
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f)

def create_genre_playlists(playlist_id: str) -> None:
    # Get all tracks from the source playlist
    tracks: List[Dict[str, Any]] = get_playlist_tracks(playlist_id)
    
    # Group tracks by genre using sets to prevent duplicates
    genre_tracks: Dict[str, Set[str]] = defaultdict(set)
    
    # Cache for artist data to reduce API calls
    artist_cache: Dict[str, List[str]] = {}
    
    # Load track genre cache
    track_cache: Dict[str, List[str]] = load_track_cache()
    cache_hits = 0
    cache_misses = 0
    
    # Process tracks in batches to avoid rate limiting
    for i, track in enumerate(tracks):
        if i % 50 == 0:  
            print(f"Processing track {i}/{len(tracks)}")
        
        if not track['track']:
            continue
            
        track_id: str = track['track']['id']
        
        # Check if track is in cache
        if track_id in track_cache:
            genres = track_cache[track_id]
            cache_hits += 1
        else:
            genres = get_track_genres(track, artist_cache)
            track_cache[track_id] = genres
            cache_misses += 1
        
        # Normalize genres and add track to each unique normalized genre
        normalized_genres: Set[str] = set()
        for genre in genres:
            normalized_genres.update(normalize_genre(genre))
        
        # Add track to each unique normalized genre
        for genre in normalized_genres:
            genre_tracks[genre].add(track_id)
        
        # Save cache periodically (every 100 tracks)
        if (i + 1) % 100 == 0:
            save_track_cache(track_cache)
            print(f"Cache stats: {cache_hits} hits, {cache_misses} misses")
        
        time.sleep(0.2)
    
    # Save final cache state
    save_track_cache(track_cache)
    print(f"Final cache stats: {cache_hits} hits, {cache_misses} misses")
    
    # Get user's playlists to check for existing ones
    existing_playlists: Dict[str, str] = get_existing_playlists()
    
    for genre, track_ids in genre_tracks.items():
        if len(track_ids) < 100:  # Skip genres with too few tracks
            continue
            
        playlist_name: str = f"{genre.title()}"
        try:
            # Check if playlist already exists
            if playlist_name in existing_playlists:
                playlist_id: str = existing_playlists[playlist_name]
                print(f"Found existing playlist '{playlist_name}', checking for existing tracks...")
                
                # Get existing tracks in playlist
                existing_tracks: Set[str] = get_playlist_track_ids(playlist_id)
                
                # Filter out tracks that already exist in the playlist
                track_ids = track_ids - existing_tracks
                print(f"Found {len(track_ids)} new tracks to add...")
            else:
                # Create new playlist if it doesn't exist
                playlist: Dict[str, Any] = sp.user_playlist_create(
                    user=sp.current_user()['id'],
                    name=playlist_name,
                    public=True
                )
                playlist_id: str = playlist['id']
                print(f"Created new playlist '{playlist_name}'")
                time.sleep(0.5)
            
            # Convert set back to list for the API call
            track_ids_list: List[str] = list(track_ids)
            
            # Add tracks to playlist in chunks of 50
            for i in range(0, len(track_ids_list), 50):
                chunk: List[str] = track_ids_list[i:i + 50]
                sp.playlist_add_items(playlist_id, chunk)
                time.sleep(0.3)
            
            print(f"Added {len(track_ids)} unique tracks to '{playlist_name}'")
        except Exception as e:
            print(f"Error updating playlist for {genre}: {str(e)}")
            time.sleep(5)  # Long delay after error
            continue

if __name__ == "__main__":
    create_genre_playlists(PLAYLIST_ID)