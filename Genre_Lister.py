import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
from typing import Dict, List, Set, Any
from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, REQUESTS_PER_SECOND
from Playlist_Tools import (
    get_playlist_tracks,
    get_track_genres,
    sp,
    RateLimiter
)

# Initialize Spotify client
sp: spotipy.Spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope='user-library-read'  # Only need read access for this
))

def list_playlist_genres(playlist_id: str) -> None:
    """List all unique genres found in a playlist"""
    # Initialize rate limiter
    rate_limiter = RateLimiter(requests_per_second=REQUESTS_PER_SECOND)
    
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
        rate_limiter.wait()
    
    # Print results
    print("\nUnique genres found in playlist:")
    for genre in sorted(unique_genres):
        print(f"- {genre}")
    print(f"\nTotal unique genres: {len(unique_genres)}")

if __name__ == "__main__":
    from config import PLAYLIST_ID
    list_playlist_genres(PLAYLIST_ID)
