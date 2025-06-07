import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
import os
from typing import Dict, List, Set, Any
from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI
from Playlist_Tools import get_artist_with_retry, sp, get_track_genres
from Genre_Tools import get_artist_genres, load_artist_cache, save_artist_cache

# Cache file path
ARTIST_CACHE_FILE = "artist_genre_cache.json"

def update_tracks_for_artist(artist_id: str, artist_genres: List[str], cache: Dict[str, List[str]]) -> None:
    """Update the cache for an artist with their genres."""
    # Update artist cache
    cache[artist_id] = artist_genres
    save_artist_cache(cache)
    print(f"\nUpdated cache for artist {artist_id}")

def print_artist_genres(artist_id: str):
    """Print all genres for a given artist and update artist cache"""
    try:
        artist = get_artist_with_retry(artist_id)
        print(f"\nGenres for {artist['name']}:")
        
        # Load current cache
        cache = load_artist_cache()
        
        if artist['genres']:
            for genre in artist['genres']:
                print(f"- {genre}")
            
            # Ask user if they want to update the cache
            response = input("\nDo you want to update the cache for this artist? (y/n): ")
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
    artist_id = "7Ln80lUS6He07XvHI8qqHH"
    print_artist_genres(artist_id)
