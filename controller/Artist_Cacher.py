"""Caches genres and country info for all artists in a playlist.

This module caches genres and country info for all artists in a playlist. 
Uses batch Spotify API requests and Wikipedia lookups to optimize API usage 
and speed up genre-based operations. Updates and saves the artist cache 
for use by other scripts.
"""

from typing import Dict, List, Set, Any
from model.spotify_client import sp, get_tracks_batch, get_artists_batch
from model.Genre_Tools import load_artist_cache, save_artist_cache, get_artist_genres, normalize_genre, deduplicate_hyphen_genres
from model.Playlist_Tools import get_playlist_track_ids, RateLimiter, format_time
import time
from model.config import PLAYLIST_ID, REQUESTS_PER_SECOND
from datetime import timedelta
from tqdm import tqdm
from model.WikipediaAPI import get_artist_country_wikidata, get_artist_genres as get_wikipedia_genres

def cache_artist_genres(playlist_id: str, progress_callback=None) -> None:
    """Cache genres for all artists in a playlist.
    
    Uses existing cache and updates it with new artist data.
    Optimized to use batch requests to reduce API calls.
    
    Args:
        playlist_id: The Spotify playlist ID to cache artists from.
        progress_callback: Optional callback function to report progress.
    """
    # Initialize rate limiter using config value
    rate_limiter = RateLimiter(requests_per_second=REQUESTS_PER_SECOND)
    
    # Load existing cache
    artist_cache: Dict[str, Dict[str, Any]] = load_artist_cache()
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
    batch_size = 50
    total_batches = len(uncached_artist_ids)
    if uncached_artist_ids:
        print("\nCaching artist genres using batch requests...")
        
        for i in tqdm(range(0, len(uncached_artist_ids), batch_size), desc="Caching artist batches"):
            batch_artist_ids = uncached_artist_ids[i:i + batch_size]
            try:
                artists = sp.artists(batch_artist_ids)
                
                for artist in artists['artists']:
                    if artist:  # Check if artist exists
                        artist_id = artist['id']
                        artist_name = artist['name']
                        genres = artist['genres']
                        # Fetch Wikipedia genres and combine
                        wikipedia_genres = get_wikipedia_genres(artist_name) or []
                        # Combine and deduplicate
                        all_genres = list(dict.fromkeys(genres + wikipedia_genres))
                        # Apply normalize_genre to each genre and flatten
                        normalized = []
                        for g in all_genres:
                            normalized.extend(normalize_genre(g))
                        # Remove duplicates while preserving order
                        all_genres = list(dict.fromkeys(normalized))
                        # Get country from Wikidata
                        country = get_artist_country_wikidata(artist_name)
                        # Add national level genres based on country
                        if country:
                            if 'Brazil' in country:
                                all_genres.append('brazilian music')
                            elif 'Japan' in country:
                                all_genres.append('Japanese Music')
                        # Deduplicate hyphen genres before saving
                        all_genres = deduplicate_hyphen_genres(all_genres)
                        # Update cache with name, genres, and country
                        artist_cache[artist_id] = {
                            'name': artist_name,
                            'genres': all_genres,
                            'country': country
                        }
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
                    
                if progress_callback:
                    progress_callback(min(i + batch_size, total_batches) / total_batches)
                
            except Exception as e:
                print(f"\nError getting batch of artists: {str(e)}")
                # Fallback to individual requests for failed batch
                for artist_id in batch_artist_ids:
                    try:
                        genres = get_artist_genres(artist_id, artist_cache)
                        # Fetch Wikipedia genres and combine
                        artist_name = sp.artist(artist_id)['name']
                        wikipedia_genres = get_wikipedia_genres(artist_name) or []
                        all_genres = list(dict.fromkeys(genres + wikipedia_genres))
                        # Apply normalize_genre to each genre and flatten
                        normalized = []
                        for g in all_genres:
                            normalized.extend(normalize_genre(g))
                        # Remove duplicates while preserving order
                        all_genres = list(dict.fromkeys(normalized))
                        # Get country from Wikidata
                        country = get_artist_country_wikidata(artist_name)
                        # Add national level genres based on country
                        if country:
                            if 'Brazil' in country:
                                all_genres.append('brazilian music')
                            elif 'Japan' in country:
                                all_genres.append('Japanese Music')
                        # Deduplicate hyphen genres before saving
                        all_genres = deduplicate_hyphen_genres(all_genres)
                        # Update cache with name, genres, and country
                        artist_cache[artist_id] = {
                            'name': artist_name,
                            'genres': all_genres,
                            'country': country
                        }
                        cache_misses += 1
                        rate_limiter.wait()
                    except Exception as e2:
                        print(f"Error getting artist {artist_id}: {str(e2)}")
                        continue
    
    # Save final cache
    save_artist_cache(artist_cache)
    
    # Print final statistics
    elapsed_time = time.time() - start_time
    print(f"\n✅ Caching completed!")
    print(f"📊 Statistics:")
    print(f"   - Total artists processed: {total_artists}")
    print(f"   - Artists already cached: {cached_count}")
    print(f"   - New artists cached: {cache_misses}")
    print(f"   - Total time: {format_time(elapsed_time)}")
    print(f"   - Average time per artist: {elapsed_time/total_artists:.2f} seconds")

def main(playlist_id: str = None, progress_callback=None):
    """Main function to cache artist genres.
    
    Args:
        playlist_id: The Spotify playlist ID to cache artists from. If None, uses PLAYLIST_ID from config.
        progress_callback: Optional callback function to report progress.
    """
    # Use provided playlist_id or fall back to config
    if playlist_id is None:
        playlist_id = PLAYLIST_ID
    
    print("\U0001F3B5 Artist Cacher")
    print("=" * 60)
    cache_artist_genres(playlist_id, progress_callback=progress_callback)

if __name__ == "__main__":
    cache_artist_genres(PLAYLIST_ID)
