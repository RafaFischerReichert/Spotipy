import json
import os
from typing import Dict, List, Set, Optional, Any
from spotify_client import sp, get_artist_with_retry
from Artist_Genres import get_custom_artist_genres

# Cache file paths
ARTIST_CACHE_FILE = "artist_genre_cache.json"

def load_artist_cache() -> Dict[str, List[str]]:
    """Load the artist genre cache from file if it exists."""
    if os.path.exists(ARTIST_CACHE_FILE):
        try:
            with open(ARTIST_CACHE_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Artist cache file corrupted, starting with empty cache")
            return {}
    return {}

def save_artist_cache(cache: Dict[str, List[str]]) -> None:
    """Save the artist genre cache to file."""
    with open(ARTIST_CACHE_FILE, 'w') as f:
        json.dump(cache, f)

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

def get_artist_genres(artist_id: str, artist_cache: Optional[Dict[str, List[str]]] = None) -> List[str]:
    """Get genres for an artist, using cache if provided."""
    # Use cache if available
    if artist_cache is not None and artist_id in artist_cache:
        return artist_cache[artist_id]
    
    # Load cache if not provided
    if artist_cache is None:
        artist_cache = load_artist_cache()
        if artist_id in artist_cache:
            return artist_cache[artist_id]
    
    # Get artist data with retry logic
    artist_data: Dict[str, Any] = get_artist_with_retry(artist_id)
    genres: List[str] = artist_data['genres']
    
    # Add custom genres if available
    custom_genres = get_custom_artist_genres(artist_id)
    genres.extend(custom_genres)
    
    # Add national level genres
    if artist_data.get('id') == '5APvSx4S3x8Gd8jfaWL4Qi':
        genres.append('brazilian music')
    elif artist_data.get('country') == 'BR':
        genres.append('brazilian music')
    elif artist_data.get('country') == 'JP':
        genres.append('Japanese Music')
    
    # Update cache
    artist_cache[artist_id] = genres
    save_artist_cache(artist_cache)
    
    return genres

def get_artist_genres_batch(artist_ids: List[str], artist_cache: Optional[Dict[str, List[str]]] = None) -> Dict[str, List[str]]:
    """Get genres for multiple artists in batch, using cache if provided."""
    if artist_cache is None:
        artist_cache = load_artist_cache()
    
    # Separate cached and uncached artists
    cached_artists = {}
    uncached_artist_ids = []
    
    for artist_id in artist_ids:
        if artist_id in artist_cache:
            cached_artists[artist_id] = artist_cache[artist_id]
        else:
            uncached_artist_ids.append(artist_id)
    
    # Batch fetch uncached artists
    if uncached_artist_ids:
        artists_data = get_artists_batch(uncached_artist_ids)
        
        for artist in artists_data:
            if artist:  # Check if artist exists
                artist_id = artist['id']
                genres = artist['genres']
                
                # Add custom genres if available
                custom_genres = get_custom_artist_genres(artist_id)
                genres.extend(custom_genres)
                
                # Add national level genres
                if artist.get('country') == 'BR':
                    genres.append('brazilian music')
                elif artist.get('country') == 'JP':
                    genres.append('Japanese Music')
                
                # Update cache
                artist_cache[artist_id] = genres
                cached_artists[artist_id] = genres
        
        # Save cache after batch update
        save_artist_cache(artist_cache)
    
    return cached_artists

def get_track_genres(track: Dict[str, Any], artist_cache: Optional[Dict[str, List[str]]] = None) -> List[str]:
    """Get genres for a track by looking up all artists, using cache if provided"""
    if not track['track']:
        return []
    
    # Get all artist IDs from the track
    artist_ids = [artist['id'] for artist in track['track']['artists']]
    
    # Get genres for all artists in batch
    artist_genres = get_artist_genres_batch(artist_ids, artist_cache)
    
    # Combine all genres
    all_genres: Set[str] = set()
    for artist_id in artist_ids:
        if artist_id in artist_genres:
            all_genres.update(artist_genres[artist_id])
    
    return list(all_genres)

def normalize_genre(genre: str) -> List[str]:
    """Normalize genre names to combine similar genres"""
    genre = genre.lower()
    result = set()  # Using set to automatically handle duplicates
    
    # Always add the original genre first
    result.add(genre)
    
    # Define genre mappings
    genre_mappings = {
        'metal': ['metal', 'djent'],
        'emo': ['emo'],
        'rap and hip hop': ['rap', 'hip hop', 'hip-hop'],
        'folk': ['folk'],
        'industrial': ['industrial'],
        'indie and alternative': ['alternative', 'indie', 'alt'],
        'rock': ['rock', 'hardcore', 'grunge'],
        'glam': ['glam'],
        'country': ['country'],
        'sertanejo': ['sertanejo'],
        'mpb': ['mpb'],
        '(Rhythm and )Blues': ['blues', 'r&b', 'rhythm and blues'],
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
        'electro and edm': ['electro', 'electronica', 'edm'],
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
    
    # Add combined tag for Japanese music
    if 'japanese music' in result:
        result.add('Anime + Japanese Music')
    
    return list(result) 