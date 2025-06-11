from typing import Dict, List, Set
from spotify_client import sp
from Genre_Tools import load_artist_cache, save_artist_cache, get_artist_genres
from Playlist_Tools import get_playlist_track_ids, get_existing_playlists, RateLimiter
import time
from config import PLAYLIST_ID, REQUESTS_PER_SECOND
from datetime import timedelta
from tqdm import tqdm

def format_time(seconds: float) -> str:
    """Format seconds into a human readable time string."""
    return str(timedelta(seconds=int(seconds)))

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

def cache_artist_genres(playlist_id: str) -> None:
    """
    Cache genres for all artists in a playlist.
    Uses existing cache and updates it with new artist data.
    Optimized to use batch requests to reduce API calls.
    """
    # Initialize rate limiter using config value
    rate_limiter = RateLimiter(requests_per_second=REQUESTS_PER_SECOND)
    
    # Load existing cache
    artist_cache: Dict[str, List[str]] = load_artist_cache()
    cache_hits: int = 0
    cache_misses: int = 0
    
    start_time = time.time()
    
    # Get all tracks from playlist
    track_ids: Set[str] = get_playlist_track_ids(playlist_id)
    total_tracks = len(track_ids)
    print(f"Found {total_tracks} tracks in playlist")
    
    # Get unique artist IDs from all tracks using batch requests
    artist_ids: Set[str] = set()
    print("\nFetching artist information from tracks using batch requests...")
    
    # Convert to list for batch processing
    track_ids_list = list(track_ids)
    
    # Process tracks in batches of 50 (Spotify API limit)
    for i in tqdm(range(0, len(track_ids_list), 50), desc="Processing track batches"):
        batch_track_ids = track_ids_list[i:i + 50]
        try:
            tracks = sp.tracks(batch_track_ids)
            for track in tracks['tracks']:
                if track:  # Check if track exists
                    for artist in track['artists']:
                        artist_ids.add(artist['id'])
            rate_limiter.wait()
        except Exception as e:
            print(f"\nError getting batch of tracks: {str(e)}")
            # Fallback to individual requests
            for track_id in batch_track_ids:
                try:
                    track = sp.track(track_id)
                    for artist in track['artists']:
                        artist_ids.add(artist['id'])
                    rate_limiter.wait()
                except Exception as e2:
                    print(f"Error getting track {track_id}: {str(e2)}")
                    continue
    
    total_artists = len(artist_ids)
    print(f"\nFound {total_artists} unique artists")
    
    # Separate cached and uncached artists
    uncached_artist_ids = [aid for aid in artist_ids if aid not in artist_cache]
    cached_count = len(artist_ids) - len(uncached_artist_ids)
    
    print(f"Artists already cached: {cached_count}")
    print(f"Artists to fetch: {len(uncached_artist_ids)}")
    
    # Cache genres for uncached artists using batch requests
    if uncached_artist_ids:
        print("\nCaching artist genres using batch requests...")
        
        # Process artists in batches of 50
        for i in tqdm(range(0, len(uncached_artist_ids), 50), desc="Caching artist batches"):
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
                        
                        # Add national level genres
                        if artist.get('country') == 'BR':
                            genres.append('brazilian music')
                        elif artist.get('country') == 'JP':
                            genres.append('Japanese Music')
                        
                        # Update cache
                        artist_cache[artist_id] = genres
                        cache_misses += 1
                
                rate_limiter.wait()
                
                # Save cache periodically and print progress
                if cache_misses % 50 == 0:
                    save_artist_cache(artist_cache)
                    elapsed_time = time.time() - start_time
                    progress = (i + 50) / len(uncached_artist_ids)
                    estimated_total_time = elapsed_time / progress if progress > 0 else 0
                    remaining_time = estimated_total_time - elapsed_time
                    
                    print(f"\nProgress: {min(i + 50, len(uncached_artist_ids))}/{len(uncached_artist_ids)} artists ({progress:.1%})")
                    print(f"Cache misses: {cache_misses}")
                    print(f"Time elapsed: {format_time(elapsed_time)}")
                    print(f"Estimated time remaining: {format_time(remaining_time)}")
                    
            except Exception as e:
                print(f"\nError getting batch of artists: {str(e)}")
                # Fallback to individual requests for failed batch
                for artist_id in batch_artist_ids:
                    try:
                        genres = get_artist_genres(artist_id, artist_cache)
                        cache_misses += 1
                        rate_limiter.wait()
                    except Exception as e2:
                        print(f"Error caching artist {artist_id}: {str(e2)}")
                        continue
    
    # Save final cache state
    save_artist_cache(artist_cache)
    total_time = time.time() - start_time
    
    print(f"\nFinal cache stats:")
    print(f"Total artists processed: {total_artists}")
    print(f"Cache hits: {cached_count}")
    print(f"Cache misses: {cache_misses}")
    print(f"Total time: {format_time(total_time)}")
    
    # Calculate request reduction
    original_requests = total_tracks + total_artists
    optimized_requests = (total_tracks // 50 + 1) + (len(uncached_artist_ids) // 50 + 1)
    reduction = ((original_requests - optimized_requests) / original_requests) * 100
    
    print(f"\nRequest optimization:")
    print(f"Original requests: {original_requests}")
    print(f"Optimized requests: {optimized_requests}")
    print(f"Request reduction: {reduction:.1f}%")

if __name__ == "__main__":
    print(f"\nCaching artists from config playlist")
    cache_artist_genres(PLAYLIST_ID)
