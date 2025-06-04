import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
from typing import Dict, List, Set, Optional, Any, Union
from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI

# Initialize Spotify client
sp: spotipy.Spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope='playlist-modify-public playlist-modify-private user-library-read'
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
                delay: int = base_delay * (2 ** attempt)  # Exponential backoff
                print(f"Request failed ({str(e)}), waiting {delay} seconds...")
                time.sleep(delay)
            else:
                raise

def get_track_genres(track: Dict[str, Any], artist_cache: Optional[Dict[str, List[str]]] = None) -> List[str]:
    """Get genres for a track by looking up all artists, using cache if provided"""
    if not track['track']:
        return []
    
    # Get genres from all artists on the track
    all_genres: Set[str] = set()
    
    for artist in track['track']['artists']:
        artist_id: str = artist['id']
        
        # Use cache if available
        if artist_cache is not None and artist_id in artist_cache:
            all_genres.update(artist_cache[artist_id])
            continue
        
        # Get artist data with retry logic
        artist_data: Dict[str, Any] = get_artist_with_retry(artist_id)
        genres: List[str] = artist_data['genres']
        
        # ARTISTS WITH NO GENRES LISTED
        # Snow Patrol
        if artist_id == '3rIZMv9rysU7JkLzEaC5Jp':
            genres.append('alternative rock')
            genres.append('rock')
            genres.append('power pop')
            genres.append('post-britpop')
            genres.append('indie rock')
        
        # Add national level genres
        if artist_data.get('country') == 'BR':
            genres.append('brazilian music')
            
        if artist_data.get('country') == 'JP':
            genres.append('Japanese Music')
        
        # Update cache if provided
        if artist_cache is not None:
            artist_cache[artist_id] = genres
        
        all_genres.update(genres)
    
    return list(all_genres)

def normalize_genre(genre: str) -> List[str]:
    """Normalize genre names to combine similar genres"""
    genre = genre.lower()
    result = set()  # Using set to automatically handle duplicates
    
    # Always add the original genre first
    result.add(genre)
    
    # Define genre mappings
    genre_mappings = {
        'metal': ['metal', 'grunge', 'djent'],
        'emo': ['emo'],
        'rap and hip hop': ['rap', 'hip hop'],
        'folk': ['folk'],
        'industrial': ['industrial'],
        'indie and alternative': ['alternative', 'indie'],
        'rock': ['rock', 'hardcore'],
        'glam': ['glam'],
        'country': ['country'],
        'sertanejo': ['sertanejo'],
        'mpb': ['mpb'],
        'blues': ['blues', 'r&b'],
        'japanese music': ['kei', 'japanese music', 'kayokyoku', 'j-pop', 'shibuya-kei', 'j-rock', 'japanese indie', 'j-rap', 'vocaloid']
    }
    
    # Check for genre mappings
    for normalized, keywords in genre_mappings.items():
        if any(keyword in genre for keyword in keywords):
            result.add(normalized)
    
    # Special cases
    special_cases = {
        'brazilian music': ['brazilian music'],
        'comedy': ['meme rap'],
        'brazilian hip hop': ['brazilian hip hop', 'brazilian trap'],
        'anime': ['anime', 'anime rap'],
        'celtic rock': ['celtic'],
        'electronic': ['electro', 'electronica', 'edm'],
        'hardcore': ['hardcore punk'],
        'drum and bass': ['bass music'],
        'medieval': ['medieval metal']
    }
    
    for normalized, matches in special_cases.items():
        if genre in matches:
            result.add(normalized)
            if normalized == 'brazilian hip hop':
                result.add('rap and hip hop')
            elif normalized == 'anime':
                result.add('Japanese Music')
            elif normalized == 'hardcore':
                result.add('hardcore punk')
            elif normalized == 'japanese indie':
                result.add('indie and alternative')
                result.add('Japanese Music')
            elif normalized == 'j-rap':
                result.add('rap and hip hop')
                result.add('Japanese Music')
            elif normalized == 'vocaloid':
                result.add('Japanese Music')
    
    # If no mappings found, we don't need to add the original genre again since we added it at the start
    
    # Add combined tag for Japanese music
    if 'japanese music' in result:
        result.add('Anime + Japanese Music')
    
    return list(result)

def get_existing_playlists() -> Dict[str, str]:
    """Get all user playlists and return a mapping of name to id"""
    user_id: str = sp.current_user()['id']
    existing_playlists: Dict[str, str] = {}
    offset: int = 0
    
    while True:
        playlists: Dict[str, Any] = sp.current_user_playlists(limit=50, offset=offset)
        for playlist in playlists['items']:
            existing_playlists[playlist['name']] = playlist['id']
        if not playlists['next']:
            break
        offset += 50
        time.sleep(0.2)
    
    return existing_playlists

def get_playlist_track_ids(playlist_id: str) -> Set[str]:
    """Get all track IDs from a playlist"""
    existing_tracks: Set[str] = set()
    offset: int = 0
    
    while True:
        results: Dict[str, Any] = sp.playlist_items(playlist_id, limit=50, offset=offset)
        for item in results['items']:
            if item['track']:
                existing_tracks.add(item['track']['id'])
        if not results['next']:
            break
        offset += 50
        time.sleep(0.3)
    
    return existing_tracks
