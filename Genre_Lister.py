import spotipy
from spotipy.oauth2 import SpotifyOAuth
from collections import defaultdict
import time
from typing import Dict, List, Set, Optional, Any
from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI

# Initialize Spotify client
sp: spotipy.Spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope='user-library-read'  # Only need read access for this
))

def get_playlist_tracks(playlist_id: str) -> List[Dict[str, Any]]:
    """Get all tracks from a playlist, handling pagination"""
    tracks: List[Dict[str, Any]] = []
    max_retries: int = 5
    base_delay: int = 1
    
    for attempt in range(max_retries):
        try:
            results: Dict[str, Any] = sp.playlist_tracks(playlist_id)
            tracks.extend(results['items'])
            
            while results['next']:
                results = sp.next(results)
                tracks.extend(results['items'])
                time.sleep(0.1)  # Rate limiting
            
            return tracks
        except Exception as e:
            if ('rate' in str(e).lower() or 'timeout' in str(e).lower()) and attempt < max_retries - 1:
                delay: int = base_delay * (2 ** attempt)
                print(f"Request failed ({str(e)}), waiting {delay} seconds...")
                time.sleep(delay)
            else:
                raise

def get_artist_with_retry(artist_id: str, max_retries: int = 3, base_delay: int = 1) -> Dict[str, Any]:
    """Get artist data with exponential backoff retry logic"""
    for attempt in range(max_retries):
        try:
            return sp.artist(artist_id)
        except Exception as e:
            if ('rate' in str(e).lower() or 'timeout' in str(e).lower()) and attempt < max_retries - 1:
                delay: int = base_delay * (2 ** attempt)
                print(f"Request failed ({str(e)}), waiting {delay} seconds...")
                time.sleep(delay)
            else:
                raise

def get_track_genres(track: Dict[str, Any], artist_cache: Optional[Dict[str, List[str]]] = None) -> List[str]:
    """Get genres for a track by looking up the artist, using cache if provided"""
    if not track['track']:
        return []
    
    artist_id: str = track['track']['artists'][0]['id']
    
    # Use cache if available
    if artist_cache is not None and artist_id in artist_cache:
        return artist_cache[artist_id]
    
    # Get artist data with retry logic
    artist: Dict[str, Any] = get_artist_with_retry(artist_id)
    genres: List[str] = artist['genres']
    
    # Update cache if provided
    if artist_cache is not None:
        artist_cache[artist_id] = genres
    
    return genres

def list_playlist_genres(playlist_id: str) -> None:
    """List all unique genres found in a playlist"""
    # Get all tracks from the playlist
    tracks: List[Dict[str, Any]] = get_playlist_tracks(playlist_id)
    
    # Set to store unique genres
    unique_genres: Set[str] = set()
    
    # Cache for artist data to reduce API calls
    artist_cache: Dict[str, List[str]] = {}
    
    # Process tracks
    for i, track in enumerate(tracks):
        if i % 50 == 0:
            print(f"Processing track {i}/{len(tracks)}")
        
        genres: List[str] = get_track_genres(track, artist_cache)
        unique_genres.update(genres)
        time.sleep(0.2)  # Rate limiting
    
    # Print results
    print("\nUnique genres found in playlist:")
    for genre in sorted(unique_genres):
        print(f"- {genre}")
    print(f"\nTotal unique genres: {len(unique_genres)}")

if __name__ == "__main__":
    from config import PLAYLIST_ID
    list_playlist_genres(PLAYLIST_ID)
