from typing import Dict, List, Set
from spotify_client import sp
from Genre_Tools import load_artist_cache, save_artist_cache, get_artist_genres
from Playlist_Tools import get_playlist_track_ids, get_existing_playlists
import time
from config import PLAYLIST_ID
from datetime import timedelta
from tqdm import tqdm

class RateLimiter:
    def __init__(self, requests_per_second: float = 0.1):
        self.requests_per_second = requests_per_second
        self.last_request_time = 0.0
        
    def wait(self):
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < (1.0 / self.requests_per_second):
            time.sleep((1.0 / self.requests_per_second) - time_since_last_request)
        self.last_request_time = time.time()

def format_time(seconds: float) -> str:
    """Format seconds into a human readable time string."""
    return str(timedelta(seconds=int(seconds)))

def cache_artist_genres(playlist_id: str) -> None:
    """
    Cache genres for all artists in a playlist.
    Uses existing cache and updates it with new artist data.
    """
    # Initialize rate limiter (10 requests per second)
    rate_limiter = RateLimiter(requests_per_second=10)
    
    # Load existing cache
    artist_cache: Dict[str, List[str]] = load_artist_cache()
    cache_hits: int = 0
    cache_misses: int = 0
    
    start_time = time.time()
    
    # Get all tracks from playlist
    track_ids: Set[str] = get_playlist_track_ids(playlist_id)
    total_tracks = len(track_ids)
    print(f"Found {total_tracks} tracks in playlist")
    
    # Get unique artist IDs from all tracks
    artist_ids: Set[str] = set()
    print("\nFetching artist information from tracks...")
    for track_id in tqdm(track_ids, desc="Processing tracks"):
        try:
            track = sp.track(track_id)
            for artist in track['artists']:
                artist_ids.add(artist['id'])
            rate_limiter.wait()
        except Exception as e:
            print(f"\nError getting track {track_id}: {str(e)}")
            continue
    
    total_artists = len(artist_ids)
    print(f"\nFound {total_artists} unique artists")
    
    # Cache genres for each artist
    print("\nCaching artist genres...")
    for i, artist_id in enumerate(tqdm(artist_ids, desc="Caching artists"), 1):
        try:
            if artist_id in artist_cache:
                cache_hits += 1
                continue
                
            # Get and cache artist genres
            genres = get_artist_genres(artist_id, artist_cache)
            cache_misses += 1
            
            # Calculate progress and time estimates
            elapsed_time = time.time() - start_time
            progress = i / total_artists
            estimated_total_time = elapsed_time / progress if progress > 0 else 0
            remaining_time = estimated_total_time - elapsed_time
            
            # Save cache periodically and print progress
            if cache_misses % 10 == 0:
                save_artist_cache(artist_cache)
                print(f"\nProgress: {i}/{total_artists} artists ({progress:.1%})")
                print(f"Cache stats: {cache_hits} hits, {cache_misses} misses")
                print(f"Time elapsed: {format_time(elapsed_time)}")
                print(f"Estimated time remaining: {format_time(remaining_time)}")
            
            rate_limiter.wait()
            
        except Exception as e:
            print(f"\nError caching artist {artist_id}: {str(e)}")
            continue
    
    # Save final cache state
    save_artist_cache(artist_cache)
    total_time = time.time() - start_time
    print(f"\nFinal cache stats:")
    print(f"Total artists processed: {total_artists}")
    print(f"Cache hits: {cache_hits}")
    print(f"Cache misses: {cache_misses}")
    print(f"Total time: {format_time(total_time)}")

if __name__ == "__main__":
    print(f"\nCaching artists from config playlist")
    cache_artist_genres(PLAYLIST_ID)
