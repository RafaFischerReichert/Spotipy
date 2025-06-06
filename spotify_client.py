import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
from typing import Dict, Any
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