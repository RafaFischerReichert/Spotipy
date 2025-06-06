import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
import os
from typing import Dict, List, Set, Any
from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI
from Playlist_Tools import get_artist_with_retry, sp, get_track_genres

# Cache file path (same as in Playlist_Creator.py)
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

def get_artist_tracks(artist_id: str) -> List[Dict[str, Any]]:
    """Get all tracks by an artist from their albums."""
    tracks = []
    albums = sp.artist_albums(artist_id, album_type='album,single', limit=50)
    
    for album in albums['items']:
        album_tracks = sp.album_tracks(album['id'])
        for track in album_tracks['items']:
            if any(artist['id'] == artist_id for artist in track['artists']):
                tracks.append(track)
    
    return tracks

def update_tracks_for_artist(artist_id: str, artist_genres: List[str], cache: Dict[str, List[str]]) -> None:
    """Update the cache for all tracks by this artist with their genres."""
    tracks = get_artist_tracks(artist_id)
    updated_count = 0
    
    for track in tracks:
        track_id = track['id']
        # Update cache with artist's genres
        cache[track_id] = artist_genres
        updated_count += 1
    
    if updated_count > 0:
        save_track_cache(cache)
        print(f"\nUpdated cache for {updated_count} tracks by this artist")

def print_artist_genres(artist_id: str):
    """Print all genres for a given artist and update track cache"""
    try:
        artist = get_artist_with_retry(artist_id)
        print(f"\nGenres for {artist['name']}:")
        
        # Load current cache
        cache = load_track_cache()
        
        if artist['genres']:
            for genre in artist['genres']:
                print(f"- {genre}")
            
            # Ask user if they want to update the cache
            response = input("\nDo you want to update the cache for all tracks by this artist? (y/n): ")
            if response.lower() == 'y':
                update_tracks_for_artist(artist_id, artist['genres'], cache)
        else:
            print("No genres found for this artist")
            # Ask user if they want to add genres manually
            response = input("\nDo you want to add genres manually? (y/n): ")
            if response.lower() == 'y':
                genres_input = input("Enter genres (comma-separated): ")
                manual_genres = [genre.strip() for genre in genres_input.split(',')]
                if manual_genres:
                    update_tracks_for_artist(artist_id, manual_genres, cache)
                    print(f"Added manual genres: {', '.join(manual_genres)}")
    except Exception as e:
        print(f"Error getting artist data: {str(e)}")

if __name__ == "__main__":
    # Example usage - replace with your artist ID
    artist_id = "3rIZMv9rysU7JkLzEaC5Jp"
    print_artist_genres(artist_id)
