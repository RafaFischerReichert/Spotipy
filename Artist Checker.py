import spotipy
from spotipy.oauth2 import SpotifyOAuth
from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI
import time

# Initialize Spotify client
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope='user-library-read'  # Only need read access for this
))

def get_artist_with_retry(artist_id: str, max_retries: int = 3, base_delay: int = 1):
    """Get artist data with exponential backoff retry logic"""
    for attempt in range(max_retries):
        try:
            return sp.artist(artist_id)
        except Exception as e:
            if 'rate' in str(e).lower() and attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)  # Exponential backoff
                print(f"Rate limited, waiting {delay} seconds...")
                time.sleep(delay)
            else:
                raise

def print_artist_genres(artist_id: str):
    """Print all genres for a given artist"""
    try:
        artist = get_artist_with_retry(artist_id)
        print(f"\nGenres for {artist['name']}:")
        if artist['genres']:
            for genre in artist['genres']:
                print(f"- {genre}")
        else:
            print("No genres found for this artist")
    except Exception as e:
        print(f"Error getting artist data: {str(e)}")

if __name__ == "__main__":
    # Example usage - replace with your artist ID
    artist_id = "0OdUWJ0sBjDrqHygGUXeCF"  # Example: Coldplay
    print_artist_genres(artist_id)
