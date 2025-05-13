import spotipy
from spotipy.oauth2 import SpotifyOAuth
from collections import defaultdict
import time
from typing import Dict, List, Set, Optional, Any, Union
from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, PLAYLIST_ID

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

def normalize_genre(genre: str) -> List[str]:
    """Normalize genre names to combine similar genres"""
    genre = genre.lower()
    result = []
    
    # Check if genre contains overarching genre names and add it as a separate genre
    if 'metal' in genre:
        result.extend(['metal'])
    if 'emo' in genre:
        result.extend(['emo'])
    if 'rap' in genre or 'hip hop' in genre:
        result.extend(['rap and hip hop'])
    if 'folk' in genre:
        result.extend(['folk'])
    if 'industrial' in genre:
        result.extend(['industrial'])
    if 'alternative' in genre or 'indie' in genre:
        result.extend(['indie and alternative'])
    if 'rock' in genre:
        result.extend(['rock'])
    if 'glam' in genre:
        result.extend(['glam'])
    if 'country' in genre:
        result.extend(['country'])
    if 'sertanejo' in genre:
        result.extend(['sertanejo'])
    if 'mpb' in genre:
        result.extend(['mpb'])
    if 'blues' in genre or 'r&b' in genre:
        result.extend(['blues'])
        
    
    if genre == 'meme rap':
        result.extend(['comedy'])
    elif genre in ['brazilian hip hop', 'brazilian trap']:
        result.extend(['brazilian hip hop', 'rap and hip hop'])
    elif genre in ['anime', 'anime rap']:
        result.extend(['anime', 'japanese music'])
    elif genre == 'celtic':
        result.extend(['celtic rock'])
    elif genre in ['electro', 'electronica', 'edm']:
        result.extend(['electronic'])
    elif genre == 'hardcore punk':
        result.extend(['hardcore punk', 'hardcore'])
    elif genre == 'bass music':
        result.extend(['drum and bass'])
    elif genre in ['kayokyoku', 'j-pop', 'shibuya-kei']:
        result.extend(['j-pop', 'japanese music'])
    elif genre == 'j-rock':
        result.extend(['j-rock', 'japanese music'])
    elif genre == 'japanese indie':
        result.extend(['japanese indie', 'japanese music', 'indie and alternative'])
    elif genre == 'j-rap':
        result.extend(['j-rap', 'rap and hip hop', 'japanese music'])
    elif genre == 'vocaloid':
        result.extend(['japanese music', 'vocaloid'])
    elif genre == 'medieval metal':
        result.extend(['medieval'])
    else:
        result.append(genre)
    
    return result

def create_genre_playlists(playlist_id: str) -> None:
    # Get all tracks from the source playlist
    tracks: List[Dict[str, Any]] = get_playlist_tracks(playlist_id)
    
    # Group tracks by genre using sets to prevent duplicates
    genre_tracks: Dict[str, Set[str]] = defaultdict(set)
    
    # Cache for artist data to reduce API calls
    artist_cache: Dict[str, List[str]] = {}
    
    # Process tracks in batches to avoid rate limiting
    for i, track in enumerate(tracks):
        if i % 50 == 0:  
            print(f"Processing track {i}/{len(tracks)}")
        
        if not track['track']:
            continue
            
        track_id: str = track['track']['id']
        genres: List[str] = get_track_genres(track, artist_cache)
        
        # Normalize genres and add track to each unique normalized genre
        normalized_genres: Set[str] = set()
        for genre in genres:
            normalized_genres.update(normalize_genre(genre))
        
        # Add track to each unique normalized genre
        for genre in normalized_genres:
            genre_tracks[genre].add(track_id)
        
        time.sleep(0.2)
    
    # Get user's playlists to check for existing ones
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
    
    for genre, track_ids in genre_tracks.items():
        if len(track_ids) < 100:  # Skip genres with too few tracks
            continue
            
        playlist_name: str = f"{genre.title()}"
        try:
            # Check if playlist already exists
            if playlist_name in existing_playlists:
                playlist_id: str = existing_playlists[playlist_name]
                print(f"Found existing playlist '{playlist_name}', checking for existing tracks...")
                
                # Get existing tracks in playlist
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
                
                # Filter out tracks that already exist in the playlist
                track_ids = track_ids - existing_tracks
                print(f"Found {len(track_ids)} new tracks to add...")
            else:
                # Create new playlist if it doesn't exist
                playlist: Dict[str, Any] = sp.user_playlist_create(
                    user=user_id,
                    name=playlist_name,
                    public=True
                )
                playlist_id: str = playlist['id']
                print(f"Created new playlist '{playlist_name}'")
                time.sleep(0.5)
            
            # Convert set back to list for the API call
            track_ids_list: List[str] = list(track_ids)
            
            # Add tracks to playlist in chunks of 50
            for i in range(0, len(track_ids_list), 50):
                chunk: List[str] = track_ids_list[i:i + 50]
                sp.playlist_add_items(playlist_id, chunk)
                time.sleep(0.3)
            
            print(f"Added {len(track_ids)} unique tracks to '{playlist_name}'")
        except Exception as e:
            print(f"Error updating playlist for {genre}: {str(e)}")
            time.sleep(5)  # Long delay after error
            continue

if __name__ == "__main__":
    create_genre_playlists(PLAYLIST_ID)