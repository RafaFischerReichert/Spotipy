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
from Genre_Tools import load_artist_cache

# Initialize Spotify client
sp: spotipy.Spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope='user-library-read'  # Only need read access for this
))

def list_playlist_genres(playlist_id: str) -> None:
    """List all unique genres found in a playlist with optimized batch processing"""
    # Initialize rate limiter
    rate_limiter = RateLimiter(requests_per_second=REQUESTS_PER_SECOND)
    
    # Get all tracks from the playlist
    tracks: List[Dict[str, Any]] = get_playlist_tracks(playlist_id)
    
    # Set to store unique genres
    unique_genres: Set[str] = set()
    
    # Load artist cache for better performance
    artist_cache: Dict[str, List[str]] = load_artist_cache()
    
    # Extract all unique artist IDs from tracks for batch processing
    all_artist_ids: Set[str] = set()
    for track in tracks:
        if track['track']:
            for artist in track['track']['artists']:
                all_artist_ids.add(artist['id'])
    
    # Pre-load uncached artists in batches
    uncached_artist_ids = [aid for aid in all_artist_ids if aid not in artist_cache]
    if uncached_artist_ids:
        print(f"Pre-loading {len(uncached_artist_ids)} uncached artists...")
        
        for i in range(0, len(uncached_artist_ids), 50):
            batch_artist_ids = uncached_artist_ids[i:i + 50]
            try:
                artists = sp.artists(batch_artist_ids)
                
                for artist in artists['artists']:
                    if artist:  # Check if artist exists
                        artist_id = artist['id']
                        genres = artist['genres']
                        
                        # Add custom genres if available
                        from Artist_Genres import get_custom_artist_genres
                        custom_genres = get_custom_artist_genres(artist_id)
                        genres.extend(custom_genres)
                        
                        # Add national level genres
                        if artist.get('country') == 'BR':
                            genres.append('brazilian music')
                        elif artist.get('country') == 'JP':
                            genres.append('Japanese Music')
                        
                        # Update cache
                        artist_cache[artist_id] = genres
                
                rate_limiter.wait()
                
            except Exception as e:
                print(f"Error getting batch of artists: {str(e)}")
                continue
    
    # Process tracks with pre-loaded cache
    print(f"Processing {len(tracks)} tracks with pre-loaded artist cache...")
    for i, track in enumerate(tracks):
        if i % 100 == 0:
            print(f"Processing track {i}/{len(tracks)}")
        
        genres: List[str] = get_track_genres(track, artist_cache)
        unique_genres.update(genres)
    
    # Print results
    print("\nUnique genres found in playlist:")
    for genre in sorted(unique_genres):
        print(f"- {genre}")
    print(f"\nTotal unique genres: {len(unique_genres)}")

if __name__ == "__main__":
    from config import PLAYLIST_ID
    list_playlist_genres(PLAYLIST_ID)
