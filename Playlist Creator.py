import spotipy
from spotipy.oauth2 import SpotifyOAuth
from collections import defaultdict
import time
from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI

# Initialize Spotify client
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope='playlist-modify-public playlist-modify-private user-library-read'
))

def get_playlist_tracks(playlist_id):
    """Get all tracks from a playlist, handling pagination"""
    tracks = []
    results = sp.playlist_tracks(playlist_id)
    tracks.extend(results['items'])
    
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
        time.sleep(0.1)  # Rate limiting
    
    return tracks

def get_artist_with_retry(artist_id, max_retries=3, base_delay=1):
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

def get_track_genres(track, artist_cache=None):
    """Get genres for a track by looking up the artist, using cache if provided"""
    if not track['track']:
        return []
    
    artist_id = track['track']['artists'][0]['id']
    
    # Use cache if available
    if artist_cache is not None and artist_id in artist_cache:
        return artist_cache[artist_id]
    
    # Get artist data with retry logic
    artist = get_artist_with_retry(artist_id)
    genres = artist['genres']
    
    # Update cache if provided
    if artist_cache is not None:
        artist_cache[artist_id] = genres
    
    return genres

def create_genre_playlists(playlist_id):
    # Get all tracks from the source playlist
    tracks = get_playlist_tracks(playlist_id)
    
    # Group tracks by genre using sets to prevent duplicates
    genre_tracks = defaultdict(set)
    
    # Cache for artist data to reduce API calls
    artist_cache = {}
    
    # Process tracks in batches to avoid rate limiting
    for i, track in enumerate(tracks):
        if i % 50 == 0:  
            print(f"Processing track {i}/{len(tracks)}")
        
        if not track['track']:
            continue
            
        track_id = track['track']['id']
        genres = get_track_genres(track, artist_cache)
        
        # Add track to each of its genres
        for genre in genres:
            genre_tracks[genre].add(track_id)
        
        time.sleep(0.2)  # Increased from 0.1 to 0.2 seconds
    
    # Get user's playlists to check for existing ones
    user_id = sp.current_user()['id']
    existing_playlists = {}
    offset = 0
    while True:
        playlists = sp.current_user_playlists(limit=50, offset=offset)
        for playlist in playlists['items']:
            existing_playlists[playlist['name']] = playlist['id']
        if not playlists['next']:
            break
        offset += 50
        time.sleep(0.2)
    
    for genre, track_ids in genre_tracks.items():
        if len(track_ids) < 30:  # Skip genres with too few tracks
            continue
            
        playlist_name = f"{genre.title()} Vibes"
        try:
            # Check if playlist already exists
            if playlist_name in existing_playlists:
                playlist_id = existing_playlists[playlist_name]
                print(f"Found existing playlist '{playlist_name}', checking for existing tracks...")
                
                # Get existing tracks in playlist
                existing_tracks = set()
                offset = 0
                while True:
                    results = sp.playlist_items(playlist_id, limit=50, offset=offset)
                    for item in results['items']:
                        if item['track']:
                            existing_tracks.add(item['track']['id'])
                    if not results['next']:
                        break
                    offset += 50
                    time.sleep(0.3)
                
                # Filter out tracks that already exist in the playlist
                track_ids = track_ids - existing_tracks
                print(f"Found {len(track_ids)} new tracks to add...")
            else:
                # Create new playlist if it doesn't exist
                playlist = sp.user_playlist_create(
                    user=user_id,
                    name=playlist_name,
                    public=True
                )
                playlist_id = playlist['id']
                print(f"Created new playlist '{playlist_name}'")
                time.sleep(0.5)
            
            # Convert set back to list for the API call
            track_ids_list = list(track_ids)
            
            # Add tracks to playlist in chunks of 50
            for i in range(0, len(track_ids_list), 50):
                chunk = track_ids_list[i:i + 50]
                sp.playlist_add_items(playlist_id, chunk)
                time.sleep(0.3)
            
            print(f"Added {len(track_ids)} unique tracks to '{playlist_name}'")
        except Exception as e:
            print(f"Error updating playlist for {genre}: {str(e)}")
            time.sleep(5)  # Long delay after error
            continue

# Usage
playlist_id = '4GQhO4MTpS8iDanLQ4vcKW'
create_genre_playlists(playlist_id)