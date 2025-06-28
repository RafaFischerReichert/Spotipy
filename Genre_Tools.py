# ---
# Genre_Tools.py
# Provides core functions for loading, saving, and managing the artist genre cache.
# Includes batch Spotify API requests, genre normalization, deduplication, and Wikipedia lookups for country and genres.
# Used by most scripts for efficient genre and artist data handling.
# ---
import json
import os
import re
from typing import Dict, List, Set, Optional, Any
from spotify_client import sp, get_artist_with_retry, get_artists_batch
from Artist_Genres import get_custom_artist_genres
from WikipediaAPI import get_artist_country_wikidata

# Cache file paths
ARTIST_CACHE_FILE = "artist_genre_cache.json"

def load_artist_cache() -> Dict[str, Dict[str, Any]]:
    """Load the artist cache from file if it exists. Cache stores genres, country, and artist name."""
    if os.path.exists(ARTIST_CACHE_FILE):
        try:
            with open(ARTIST_CACHE_FILE, 'r') as f:
                cache_data = json.load(f)
                # Handle migration from old format
                migrated_cache = {}
                for artist_id, data in cache_data.items():
                    if isinstance(data, list):
                        # Old format - convert to new format
                        migrated_cache[artist_id] = {
                            'name': None,  # Will be populated when accessed
                            'genres': data,
                            'country': None
                        }
                    elif isinstance(data, dict):
                        # Check if this is the new format with name
                        if 'name' not in data:
                            # Old dict format without name - add None for name
                            data['name'] = None
                        migrated_cache[artist_id] = data
                    else:
                        # Unknown format - skip
                        continue
                return migrated_cache
        except json.JSONDecodeError:
            print("Artist cache file corrupted, starting with empty cache")
            return {}
    return {}

def save_artist_cache(cache: Dict[str, Dict[str, Any]]) -> None:
    """Save the artist cache to file."""
    with open(ARTIST_CACHE_FILE, 'w') as f:
        json.dump(cache, f)

def get_artist_name_from_cache(artist_id: str, artist_cache: Optional[Dict[str, Dict[str, Any]]] = None) -> str:
    """Get artist name from cache, falling back to Spotify API if not cached."""
    if artist_cache is None:
        artist_cache = load_artist_cache()
    
    if artist_id in artist_cache:
        cached_name = artist_cache[artist_id].get('name')
        if cached_name:
            return cached_name
    
    # Fallback to Spotify API if not in cache or name is None
    try:
        artist_data = get_artist_with_retry(artist_id)
        artist_name = artist_data['name']
        
        # Update cache with the name if it wasn't there
        if artist_id in artist_cache:
            artist_cache[artist_id]['name'] = artist_name
            save_artist_cache(artist_cache)
        else:
            # Create new cache entry
            artist_cache[artist_id] = {
                'name': artist_name,
                'genres': artist_data.get('genres', []),
                'country': None
            }
            save_artist_cache(artist_cache)
        
        return artist_name
    except Exception as e:
        print(f"Error getting artist name for {artist_id}: {e}")
        return f"Unknown Artist ({artist_id})"

def get_artist_genres(artist_id: str, artist_cache: Optional[Dict[str, Dict[str, Any]]] = None) -> List[str]:
    """Get genres for an artist, using cache if provided."""
    # Use cache if available
    if artist_cache is not None and artist_id in artist_cache:
        return artist_cache[artist_id]['genres']
    
    # Load cache if not provided
    if artist_cache is None:
        artist_cache = load_artist_cache()
        if artist_id in artist_cache:
            return artist_cache[artist_id]['genres']
    
    # Get artist data with retry logic
    artist_data: Dict[str, Any] = get_artist_with_retry(artist_id)
    artist_name = artist_data['name']
    genres: List[str] = artist_data['genres']
    
    # Add custom genres if available
    custom_genres = get_custom_artist_genres(artist_id)
    genres.extend(custom_genres)
    
    # Get country from Wikipedia/Wikidata
    country = get_artist_country_wikidata(artist_name)
    
    # Add national level genres based on Wikipedia country
    if country:
        genres_lower = [g.lower() for g in genres]
        if 'brazil' in country and 'brazilian music' not in genres_lower:
            genres.append('Brazilian Music')
        elif 'japan' in country and 'japanese music' not in genres_lower:
            genres.append('Japanese Music')
    
    # Deduplicate hyphen genres before saving
    genres = deduplicate_hyphen_genres(genres)
    
    # Update cache with name, genres and Wikipedia country
    artist_cache[artist_id] = {
        'name': artist_name,
        'genres': genres,
        'country': country
    }
    save_artist_cache(artist_cache)
    
    return genres

def get_artist_genres_batch(artist_ids: List[str], artist_cache: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, List[str]]:
    """Get genres for multiple artists in batch, using cache if provided."""
    if artist_cache is None:
        artist_cache = load_artist_cache()
    
    # Separate cached and uncached artists
    cached_artists = {}
    uncached_artist_ids = []
    
    for artist_id in artist_ids:
        if artist_id in artist_cache:
            cached_artists[artist_id] = artist_cache[artist_id]['genres']
        else:
            uncached_artist_ids.append(artist_id)
    
    # Batch fetch uncached artists
    if uncached_artist_ids:
        artists_data = get_artists_batch(uncached_artist_ids)
        
        for artist in artists_data:
            if artist:  # Check if artist exists
                artist_id = artist['id']
                artist_name = artist['name']
                genres = artist['genres']
                
                # Add custom genres if available
                custom_genres = get_custom_artist_genres(artist_id)
                genres.extend(custom_genres)
                
                # Get country from Wikipedia/Wikidata
                country = get_artist_country_wikidata(artist_name)
                
                # Add national level genres based on Wikipedia country
                genres_lower = [g.lower() for g in genres]
                if country:
                    if 'brazil' in country and 'brazilian music' not in genres_lower:
                        genres.append('Brazilian Music')
                    elif 'japan' in country and 'japanese music' not in genres_lower:
                        genres.append('Japanese Music')
                
                # Deduplicate hyphen genres before saving
                genres = deduplicate_hyphen_genres(genres)
                
                # Update cache with name, genres and Wikipedia country
                artist_cache[artist_id] = {
                    'name': artist_name,
                    'genres': genres,
                    'country': country
                }
                cached_artists[artist_id] = genres
        
        # Save cache after batch update
        save_artist_cache(artist_cache)
    
    return cached_artists

def get_track_genres(track: Dict[str, Any], artist_cache: Optional[Dict[str, Dict[str, Any]]] = None) -> List[str]:
    """Get genres for a track by looking up all artists, using cache if provided."""
    if not track['track']:
        return []
    
    # Get all artist IDs from the track
    artist_ids = [artist['id'] for artist in track['track']['artists']]
    
    # Get genres for all artists in batch
    artist_genres = get_artist_genres_batch(artist_ids, artist_cache)
    
    # Combine all genres
    all_genres: Set[str] = set()
    is_brazilian = False
    is_japanese = False
    is_scandinavian = False
    
    for artist in track['track']['artists']:
        artist_id = artist['id']
        if artist_id in artist_genres:
            all_genres.update(artist_genres[artist_id])
        
        # Check cached country info for tagging
        if artist_cache and artist_id in artist_cache:
            country = artist_cache[artist_id].get('country')
            if country:
                if 'Brazil' in country:
                    is_brazilian = True
                elif 'Japan' in country:
                    is_japanese = True
                elif country in ['Sweden', 'Norway', 'Iceland', 'Finland', 'Denmark']:
                    is_scandinavian = True
    
    if is_brazilian:
        # Only add if not already present (case-insensitive)
        if not any(g.lower() == 'brazilian music' for g in all_genres):
            all_genres.add('Brazilian Music')
    if is_japanese:
        if not any(g.lower() == 'japanese music' for g in all_genres):
            all_genres.add('Japanese Music')
    if is_scandinavian:
        # Check if any of the track's genres normalize to 'metal'
        is_metal = any('metal' in normalize_genre(g) for g in all_genres)
        if is_metal:
            all_genres.add('scandinavian metal')
    
    return list(all_genres)

def normalize_genre(genre: str) -> List[str]:
    """Normalize genre names to combine similar genres"""
    # Drop unwanted tags
    if genre.strip().lower() in ["name", "genres"]:
        return []
    # First, clean the genre by removing " music" from the end (except Brazilian and Japanese Music)
    original_genre = genre
    if genre.lower() not in ['brazilian music', 'japanese music']:
        genre = re.sub(r' music$', '', genre, flags=re.IGNORECASE).strip()
    
    genre_lower = genre.lower()
    result = set()  # Using set to automatically handle duplicates
    
    # For Brazilian and Japanese, always add the title-case version
    if genre_lower == 'brazilian music':
        result.add('Brazilian Music')
    if genre_lower == 'japanese music':
        result.add('Japanese Music')
        result.add('Anime + Japanese Music')
    
    # Define genre mappings
    genre_mappings = {
        'brazilian music': ['brazilian'],
        'metal': ['metal', 'djent'],
        'emo': ['emo'],
        'rap and hip hop': ['rap', 'hip hop', 'hip-hop'],
        'folk': ['folk'],
        'punk': ['punk'],
        'industrial': ['industrial'],
        'indie and alternative': ['alternative', 'indie', 'alt'],
        'rock': ['rock', 'hardcore', 'grunge', 'metal'],
        'glam': ['glam'],
        'country': ['country'],
        'sertanejo': ['sertanejo'],
        'mpb': ['mpb'],
        '(Rhythm and )Blues': ['blues', 'r&b', 'rhythm and blues'],
        'Japanese Music': ['kei', 'japanese music', 'kayokyoku', 'j-pop', 'shibuya-kei', 'j-rock', 'anime', 'japanese indie', 'j-rap', 'vocaloid'],
        'comedy': ['comedy', 'meme']
    }
    
    # Special cases (these should remove the original genre)
    special_cases = {
        'anime': ['anime rap'],
        'electro and edm': ['electro', 'electronica', 'edm'],
        'hardcore': ['hardcore punk'],
        'drum and bass': ['bass music'],
        'mpb': ['música popular brasileira'],
        '(Rhythm And )Blues': ['contemporary r&b'],
        'rap and hip hop': ['hip-hop', 'hip hop']
    }
    
    # Check if this is a special case first
    is_special_case = False
    for normalized, matches in special_cases.items():
        if genre_lower in matches:
            result.add(normalized)
            is_special_case = True
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
    
    # Check for genre mappings (only if not a special case)
    is_mapping_case = False
    if not is_special_case:
        for normalized, keywords in genre_mappings.items():
            if any(keyword in genre_lower for keyword in keywords):
                result.add(normalized)
                is_mapping_case = True
    
    # Add combined tag for Japanese music
    if 'japanese music' in genre_lower or 'Japanese Music' in result:
        result.add('Anime + Japanese Music')
    
    # Preserve original genre for mapping cases or when no mappings found
    if is_mapping_case or (not is_special_case and not is_mapping_case):
        result.add(genre)
    
    # For special cases, ensure the original genre is removed
    if is_special_case and genre in result:
        result.remove(genre)
    
    return list(result)

def deduplicate_hyphen_genres(genres: List[str]) -> List[str]:
    """Remove duplicate genres that differ only by hyphens"""
    # Create a mapping of normalized genre names to original genres
    normalized_map = {}
    
    for genre in genres:
        # Normalize by removing hyphens and converting to lowercase
        normalized = genre.lower().replace('-', ' ')
        normalized = ' '.join(normalized.split())  # Remove extra spaces
        
        # Keep the first occurrence of each normalized genre
        if normalized not in normalized_map:
            normalized_map[normalized] = genre
    
    # Return the deduplicated list
    return list(normalized_map.values())

def should_track_be_in_playlist(track_genres: List[str], playlist_genre: str) -> bool:
    """Check if a track should be in a specific genre playlist"""
    # Normalize the playlist genre
    playlist_genre_lower = playlist_genre.lower()
    
    # Check each track genre
    for track_genre in track_genres:
        normalized_track_genres = normalize_genre(track_genre)
        
        # Check for exact match
        for norm_genre in normalized_track_genres:
            if norm_genre.lower() == playlist_genre_lower:
                return True
    
    return False 