# ---
# Playlist_Tools.py
# Provides core playlist management utilities, including batch fetching, genre grouping, and optimized API usage for playlist creation and updates.
# Used by most scripts for efficient playlist and track management.
# ---
import time
from typing import Dict, List, Set, Any
from config import REQUESTS_PER_SECOND
from spotify_client import sp
from Genre_Tools import get_track_genres, load_artist_cache, save_artist_cache, normalize_genre, get_artist_genres
from collections import defaultdict
from WikipediaAPI import get_artist_country_wikidata

class RateLimiter:
    def __init__(self, requests_per_second: float = REQUESTS_PER_SECOND):
        self.requests_per_second = requests_per_second
        self.last_request_time = 0.0
        
    def wait(self):
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
            # Use maximum limit to reduce pagination requests
            results: Dict[str, Any] = sp.playlist_tracks(playlist_id, limit=100)
            tracks.extend(results['items'])
            
            while results['next']:
                results = sp.next(results)
                tracks.extend(results['items'])
                rate_limiter.wait()
            
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
                        genres = artist['genres']
                        
                        # Add custom genres if available
                        from Artist_Genres import get_custom_artist_genres
                        custom_genres = get_custom_artist_genres(artist_id)
                        genres.extend(custom_genres)
                        
                        # Get country from Wikipedia/Wikidata
                        country = get_artist_country_wikidata(artist['name'])
                        
                        # Add national level genres based on Wikipedia country
                        if country:
                            if 'Brazil' in country:
                                genres.append('brazilian music')
                            elif 'Japan' in country:
                                genres.append('Japanese Music')
                        
                        # Update cache
                        artist_cache[artist_id] = {
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
    """Process tracks in optimized batches with efficient genre extraction"""
    genre_tracks: Dict[str, Set[str]] = defaultdict(set)
    track_genres_map: Dict[str, List[str]] = {}

    print(f"Processing {len(tracks)} tracks in optimized batches of {batch_size}...")

    # Step 1: Collect raw genres for all tracks
    for track in tracks:
        if track['track']:
            track_id = track['track']['id']
            raw_genres = get_track_genres(track, artist_cache)
            track_genres_map[track_id] = raw_genres

    # Step 2: Create a normalization map for all unique raw genres
    all_raw_genres = set(g for genres in track_genres_map.values() for g in genres)
    normalization_map = {genre: normalize_genre(genre) for genre in all_raw_genres}

    # Step 3: Populate genre_tracks using the normalization map
    for track in tracks:
        if track['track']:
            track_id = track['track']['id']
            raw_genres = track_genres_map.get(track_id, [])
            
            for raw_genre in raw_genres:
                normalized_genres = normalization_map.get(raw_genre, [])
                for normalized_genre in normalized_genres:
                    genre_tracks[normalized_genre].add(track_id)
    
    return genre_tracks
