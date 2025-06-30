"""Core playlist management utilities.

This module provides core playlist management utilities, including batch fetching, 
genre grouping, and optimized API usage for playlist creation and updates. 
Used by most scripts for efficient playlist and track management.
"""

import time
import re
from typing import Dict, List, Set, Any
from model.config import REQUESTS_PER_SECOND
from model.spotify_client import sp, get_artists_batch, get_tracks_batch
from model.Genre_Tools import get_track_genres, load_artist_cache, save_artist_cache, normalize_genre, get_artist_genres
from collections import defaultdict
from model.WikipediaAPI import get_artist_country_wikidata
from model.Artist_Genres import get_custom_artist_genres

def extract_playlist_id_from_url(url: str) -> str:
    """Extract playlist ID from a Spotify playlist URL.
    
    Args:
        url: Spotify playlist URL (e.g., https://open.spotify.com/playlist/4GQhO4MTpS8iDanLQ4vcKW?si=a500f459aba34f74)
        
    Returns:
        The playlist ID (e.g., 4GQhO4MTpS8iDanLQ4vcKW)
        
    Raises:
        ValueError: If the URL format is invalid or playlist ID cannot be extracted
    """
    # Pattern to match playlist ID in Spotify URL
    pattern = r'playlist/([a-zA-Z0-9]+)'
    match = re.search(pattern, url)
    
    if match:
        return match.group(1)
    else:
        raise ValueError("Invalid Spotify playlist URL format. Expected format: https://open.spotify.com/playlist/PLAYLIST_ID")

class RateLimiter:
    """Rate limiter for API requests to respect rate limits.
    
    Attributes:
        requests_per_second: Maximum requests allowed per second.
        last_request_time: Timestamp of the last request made.
    """
    
    def __init__(self, requests_per_second: float = REQUESTS_PER_SECOND):
        """Initialize the rate limiter.
        
        Args:
            requests_per_second: Maximum requests allowed per second. Defaults to REQUESTS_PER_SECOND.
        """
        self.requests_per_second = requests_per_second
        self.last_request_time = 0.0
        
    def wait(self):
        """Wait if necessary to respect the rate limit."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < (1.0 / self.requests_per_second):
            time.sleep((1.0 / self.requests_per_second) - time_since_last_request)
        self.last_request_time = time.time()

# Cache file path
ARTIST_CACHE_FILE = "artist_genre_cache.json"

def get_playlist_tracks(playlist_id: str) -> List[Dict[str, Any]]:
    """Get all tracks from a playlist, handling pagination with optimized batch size"""
    tracks: List[Dict[str, Any]] = []
    max_retries: int = 5
    base_delay: int = 1
    rate_limiter = RateLimiter(requests_per_second=REQUESTS_PER_SECOND)
    
    for attempt in range(max_retries):
        try:
            # Apply rate limiting before the initial request
            rate_limiter.wait()
            
            # Use maximum limit to reduce pagination requests
            results: Dict[str, Any] = sp.playlist_tracks(playlist_id, limit=100)
            tracks.extend(results['items'])
            
            while results['next']:
                rate_limiter.wait()
                results = sp.next(results)
                tracks.extend(results['items'])
            
            return tracks
        except Exception as e:
            if ('rate' in str(e).lower() or 'timeout' in str(e).lower()) and attempt < max_retries - 1:
                delay: int = base_delay * (2 ** attempt)
                print(f"Request failed ({str(e)}), waiting {delay} seconds...")
                time.sleep(delay)
            else:
                raise

def get_existing_playlists() -> Dict[str, str]:
    """Get all user playlists and return a mapping of name to id with optimized batch size"""
    user_id: str = sp.current_user()['id']
    existing_playlists: Dict[str, str] = {}
    offset: int = 0
    rate_limiter = RateLimiter(requests_per_second=REQUESTS_PER_SECOND)
    
    while True:
        # Use maximum limit to reduce pagination requests
        playlists: Dict[str, Any] = sp.current_user_playlists(limit=50, offset=offset)
        for playlist in playlists['items']:
            existing_playlists[playlist['name']] = playlist['id']
        if not playlists['next']:
            break
        offset += 50
        rate_limiter.wait()
    
    return existing_playlists

def get_playlist_track_ids(playlist_id: str) -> Set[str]:
    """Get all track IDs from a playlist with optimized batch size"""
    existing_tracks: Set[str] = set()
    offset: int = 0
    rate_limiter = RateLimiter(requests_per_second=REQUESTS_PER_SECOND)
    
    while True:
        # Use maximum limit to reduce pagination requests
        results: Dict[str, Any] = sp.playlist_items(playlist_id, limit=100, offset=offset)
        for item in results['items']:
            if item['track']:
                existing_tracks.add(item['track']['id'])
        if not results['next']:
            break
        offset += 100
        rate_limiter.wait()
    
    return existing_tracks

def get_tracks_batch(track_ids: List[str], batch_size: int = 50) -> List[Dict]:
    """Get multiple tracks in a single API call to reduce requests."""
    all_tracks = []
    rate_limiter = RateLimiter(requests_per_second=REQUESTS_PER_SECOND)
    
    for i in range(0, len(track_ids), batch_size):
        batch = track_ids[i:i + batch_size]
        try:
            tracks = sp.tracks(batch)
            all_tracks.extend(tracks['tracks'])
            rate_limiter.wait()
        except Exception as e:
            print(f"\nError getting batch of tracks: {str(e)}")
            # Fallback to individual requests for failed batch
            for track_id in batch:
                try:
                    track = sp.track(track_id)
                    all_tracks.append(track)
                    rate_limiter.wait()
                except Exception as e2:
                    print(f"Error getting track {track_id}: {str(e2)}")
                    continue
    
    return all_tracks

def get_artists_batch(artist_ids: List[str], batch_size: int = 50) -> List[Dict]:
    """Get multiple artists in a single API call to reduce requests."""
    all_artists = []
    rate_limiter = RateLimiter(requests_per_second=REQUESTS_PER_SECOND)
    
    for i in range(0, len(artist_ids), batch_size):
        batch = artist_ids[i:i + batch_size]
        try:
            artists = sp.artists(batch)
            all_artists.extend(artists['artists'])
            rate_limiter.wait()
        except Exception as e:
            print(f"\nError getting batch of artists: {str(e)}")
            # Fallback to individual requests for failed batch
            for artist_id in batch:
                try:
                    artist = sp.artist(artist_id)
                    all_artists.append(artist)
                    rate_limiter.wait()
                except Exception as e2:
                    print(f"Error getting artist {artist_id}: {str(e2)}")
                    continue
    
    return all_artists

def create_genre_playlists(playlist_id: str) -> None:
    """Create genre playlists with optimized batch processing and caching"""
    # Initialize rate limiter
    rate_limiter = RateLimiter(requests_per_second=REQUESTS_PER_SECOND)
    
    # Get all tracks from the source playlist
    tracks: List[Dict[str, Any]] = get_playlist_tracks(playlist_id)
    
    # Group tracks by genre using sets to prevent duplicates
    genre_tracks: Dict[str, Set[str]] = defaultdict(set)
    
    # Load artist cache
    artist_cache: Dict[str, Dict[str, Any]] = load_artist_cache()
    
    # Extract all unique artist IDs from tracks
    all_artist_ids: Set[str] = set()
    for track in tracks:
        if track['track']:
            for artist in track['track']['artists']:
                all_artist_ids.add(artist['id'])
    
    # Batch fetch uncached artists
    uncached_artist_ids = [aid for aid in all_artist_ids if aid not in artist_cache]
    if uncached_artist_ids:
        print(f"Fetching {len(uncached_artist_ids)} uncached artists in batches...")
        
        for i in range(0, len(uncached_artist_ids), 50):
            batch_artist_ids = uncached_artist_ids[i:i + 50]
            try:
                artists = sp.artists(batch_artist_ids)
                
                for artist in artists['artists']:
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
                        if country:
                            if 'Brazil' in country:
                                genres.append('brazilian music')
                            elif 'Japan' in country:
                                genres.append('Japanese Music')
                        
                        # Update cache with name, genres, and country
                        artist_cache[artist_id] = {
                            'name': artist_name,
                            'genres': genres,
                            'country': country
                        }
                
                rate_limiter.wait()
                
            except Exception as e:
                print(f"Error getting batch of artists: {str(e)}")
                # Fallback to individual requests
                for artist_id in batch_artist_ids:
                    try:
                        genres = get_artist_genres(artist_id, artist_cache)
                        rate_limiter.wait()
                    except Exception as e2:
                        print(f"Error getting artist {artist_id}: {str(e2)}")
                        continue
    
    # Process tracks in batches for better performance
    print(f"Processing {len(tracks)} tracks with pre-loaded artist cache...")
    
    # Use optimized batch processing
    genre_tracks = process_tracks_batch_optimized(tracks, artist_cache, batch_size=100)
    
    # Save final cache state
    save_artist_cache(artist_cache)
    
    return genre_tracks

def process_tracks_batch_optimized(tracks: List[Dict[str, Any]], artist_cache: Dict[str, Dict[str, Any]], batch_size: int = 100) -> Dict[str, Set[str]]:
    """Process tracks in optimized batches to group by genre"""
    genre_tracks: Dict[str, Set[str]] = defaultdict(set)
    
    # Process tracks in batches
    for i in range(0, len(tracks), batch_size):
        batch = tracks[i:i + batch_size]
        
        for track in batch:
            if track['track']:
                track_id = track['track']['id']
                track_genres = get_track_genres(track, artist_cache)
                
                # Add track to each of its genres
                for genre in track_genres:
                    genre_tracks[genre].add(track_id)
    
    return genre_tracks

def format_time(seconds: float) -> str:
    """Format seconds into a human readable time string.
    
    Args:
        seconds: Number of seconds to format.
        
    Returns:
        Formatted time string in HH:MM:SS format.
    """
    from datetime import timedelta
    return str(timedelta(seconds=int(seconds)))

def find_matching_playlists(genre: str, existing_playlists: Dict[str, str]) -> List[str]:
    """Find playlists that match a given genre exactly"""
    matching_playlists = []
    normalized_genres = normalize_genre(genre)
    
    for playlist_name, playlist_id in existing_playlists.items():
        playlist_name_lower = playlist_name.lower()
        
        # Check for exact matches with normalized genres
        for norm_genre in normalized_genres:
            # Exact match: playlist name should exactly match the normalized genre
            if playlist_name_lower == norm_genre.lower():
                matching_playlists.append(playlist_id)
                break
    
    return matching_playlists

def get_playlist_genre(playlist_name: str) -> str:
    """Extract the genre from playlist name"""
    # Remove common prefixes/suffixes and get the main genre
    name_lower = playlist_name.lower()
    
    # Common genre playlist patterns
    genre_patterns = [
        'metal', 'rock', 'pop', 'hip hop', 'rap', 'jazz', 'classical', 'electronic',
        'folk', 'country', 'r&b', 'blues', 'reggae', 'punk', 'indie', 'alternative',
        'brazilian', 'japanese', 'anime', 'emo', 'industrial', 'glam', 'sertanejo',
        'mpb', 'hardcore', 'celtic', 'medieval', 'comedy', 'electro', 'edm'
    ]
    
    for pattern in genre_patterns:
        if pattern in name_lower:
            return pattern
    
    # If no pattern matches, return the playlist name as is
    return name_lower

def identify_genre_playlists(existing_playlists: Dict[str, str]) -> Dict[str, str]:
    """Identify playlists that are likely genre playlists"""
    genre_playlists = {}
    
    genre_keywords = [
        'metal', 'rock', 'pop', 'hip hop', 'rap', 'jazz', 'classical', 'electronic',
        'folk', 'country', 'r&b', 'blues', 'reggae', 'punk', 'indie', 'alternative',
        'brazilian', 'japanese', 'anime', 'emo', 'industrial', 'glam', 'sertanejo',
        'mpb', 'hardcore', 'celtic', 'medieval', 'comedy', 'electro', 'edm'
    ]
    
    for playlist_name, playlist_id in existing_playlists.items():
        name_lower = playlist_name.lower()
        
        # Check if playlist name contains genre keywords
        for keyword in genre_keywords:
            if keyword in name_lower:
                genre_playlists[playlist_name] = playlist_id
                break
    
    return genre_playlists
