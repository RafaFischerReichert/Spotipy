# ---
# spotify_client.py
# Initializes the Spotify API client and provides utility functions for robust API access.
# Includes retry logic for artist lookups and is used by most scripts for Spotify API operations.
# ---
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
from typing import Dict, Any, List
from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI

# Initialize Spotify client
sp: spotipy.Spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope='playlist-modify-public playlist-modify-private user-library-read'
))

def get_artist_with_retry(artist_id: str, max_retries: int = 3, base_delay: int = 1) -> Dict[str, Any]:
    """Get artist data with exponential backoff retry logic"""
    for attempt in range(max_retries):
        try:
            return sp.artist(artist_id)
        except Exception as e:
            if ('rate' in str(e).lower() or 'timeout' in str(e).lower()) and attempt < max_retries - 1:
                delay: int = base_delay * (2 ** attempt)  # Exponential backoff
                print(f"Request failed ({str(e)}), waiting {delay} seconds...")
                time.sleep(delay)
            else:
                raise

def get_artists_batch(artist_ids: List[str], batch_size: int = 50) -> List[Dict[str, Any]]:
    """Get multiple artists in a single API call to reduce requests."""
    all_artists = []
    
    for i in range(0, len(artist_ids), batch_size):
        batch = artist_ids[i:i + batch_size]
        try:
            artists = sp.artists(batch)
            all_artists.extend(artists['artists'])
        except Exception as e:
            print(f"Error getting batch of artists: {str(e)}")
            # Fallback to individual requests for failed batch
            for artist_id in batch:
                try:
                    artist = sp.artist(artist_id)
                    all_artists.append(artist)
                except Exception as e2:
                    print(f"Error getting artist {artist_id}: {str(e2)}")
                    continue
    
    return all_artists

def get_tracks_batch(track_ids: List[str], batch_size: int = 50) -> List[Dict[str, Any]]:
    """Get multiple tracks in a single API call to reduce requests."""
    all_tracks = []
    
    for i in range(0, len(track_ids), batch_size):
        batch = track_ids[i:i + batch_size]
        try:
            tracks = sp.tracks(batch)
            all_tracks.extend(tracks['tracks'])
        except Exception as e:
            print(f"Error getting batch of tracks: {str(e)}")
            # Fallback to individual requests for failed batch
            for track_id in batch:
                try:
                    track = sp.track(track_id)
                    all_tracks.append(track)
                except Exception as e2:
                    print(f"Error getting track {track_id}: {str(e2)}")
                    continue
    
    return all_tracks 