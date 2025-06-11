from typing import List, Dict, Any
import json
import os
import time
from spotify_client import sp, get_artist_with_retry
from Genre_Tools import get_track_genres, load_track_cache, save_track_cache, get_artist_genres
from Artist_Genres import get_custom_artist_genres
from config import REQUESTS_PER_SECOND
from Playlist_Tools import RateLimiter

# Cache file path (same as in other files)
CACHE_FILE = "track_genre_cache.json"

def load_track_cache() -> Dict[str, List[str]]:
    """Load the track genre cache from file if it exists."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Cache file corrupted, starting with empty cache")
            return {}
    return {}

def save_track_cache(cache: Dict[str, List[str]]) -> None:
    """Save the track genre cache to file."""
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f)

def get_artist_albums_batch(artist_id: str) -> List[Dict[str, Any]]:
    """Get all albums by an artist with optimized pagination."""
    albums = []
    rate_limiter = RateLimiter(requests_per_second=REQUESTS_PER_SECOND)
    
    try:
        # Use maximum limit to reduce pagination requests
        results = sp.artist_albums(artist_id, album_type='album,single', limit=50)
        albums.extend(results['items'])
        
        while results['next']:
            results = sp.next(results)
            albums.extend(results['items'])
            rate_limiter.wait()
            
    except Exception as e:
        print(f"Error getting albums for artist {artist_id}: {str(e)}")
    
    return albums

def get_album_tracks_batch(album_ids: List[str], batch_size: int = 20) -> List[Dict[str, Any]]:
    """Get tracks from multiple albums in batches to reduce API calls."""
    all_tracks = []
    rate_limiter = RateLimiter(requests_per_second=REQUESTS_PER_SECOND)
    
    for i in range(0, len(album_ids), batch_size):
        batch_album_ids = album_ids[i:i + batch_size]
        
        for album_id in batch_album_ids:
            try:
                album_tracks = sp.album_tracks(album_id, limit=50)
                all_tracks.extend(album_tracks['items'])
                
                # Handle pagination for large albums
                while album_tracks['next']:
                    album_tracks = sp.next(album_tracks)
                    all_tracks.extend(album_tracks['items'])
                
                rate_limiter.wait()
                
            except Exception as e:
                print(f"Error getting tracks for album {album_id}: {str(e)}")
                continue
    
    return all_tracks

def get_artist_tracks(artist_id: str) -> List[Dict[str, Any]]:
    """Get all tracks by an artist from their albums with optimized batch processing."""
    tracks = []
    rate_limiter = RateLimiter(requests_per_second=REQUESTS_PER_SECOND)
    
    try:
        # Get all albums in one batch
        albums = get_artist_albums_batch(artist_id)
        
        if not albums:
            return tracks
        
        # Extract album IDs
        album_ids = [album['id'] for album in albums]
        
        # Get all tracks from all albums in batches
        all_album_tracks = get_album_tracks_batch(album_ids)
        
        # Filter tracks by the specific artist
        for track in all_album_tracks:
            if any(artist['id'] == artist_id for artist in track['artists']):
                tracks.append({'track': track})  # Wrap in same format as playlist tracks
        
        rate_limiter.wait()
        
    except Exception as e:
        print(f"Error getting tracks for artist {artist_id}: {str(e)}")
    
    return tracks

def update_cache_for_all_artists() -> None:
    """Update the cache for all artists in the genre mappings with optimized batch processing."""
    # Load current cache
    cache = load_track_cache()
    artist_cache = {}  # Cache for artist data
    total_updated = 0
    
    # Get all artist IDs from the mappings
    from Artist_Genres import ARTIST_GENRE_MAPPINGS
    artist_ids = list(ARTIST_GENRE_MAPPINGS.keys())
    
    print(f"\nUpdating cache for {len(artist_ids)} artists...")
    
    # Batch process artists for better efficiency
    batch_size = 10  # Process 10 artists at a time
    for i in range(0, len(artist_ids), batch_size):
        batch_artist_ids = artist_ids[i:i + batch_size]
        batch_artists = []
        
        # Get artist info for the batch
        for artist_id in batch_artist_ids:
            try:
                artist = get_artist_with_retry(artist_id)
                batch_artists.append((artist_id, artist))
            except Exception as e:
                print(f"Error getting artist {artist_id}: {str(e)}")
                continue
        
        # Process each artist in the batch
        for artist_id, artist in batch_artists:
            try:
                artist_name = artist['name']
                print(f"\nProcessing {i + batch_artists.index((artist_id, artist)) + 1}/{len(artist_ids)}: {artist_name}")
                
                # Get all tracks for this artist
                tracks = get_artist_tracks(artist_id)
                print(f"Found {len(tracks)} tracks")
                
                # Update cache for each track
                for track in tracks:
                    if not track['track']:
                        continue
                        
                    track_id = track['track']['id']
                    
                    # Skip if already in cache
                    if track_id in cache:
                        continue
                    
                    # Get genres using our custom function
                    genres = get_track_genres(track, artist_cache)
                    if genres:  # Only update if we got genres
                        cache[track_id] = genres
                        total_updated += 1
                
            except Exception as e:
                print(f"Error processing artist {artist_id}: {str(e)}")
                continue
        
        # Save cache periodically (every batch)
        save_track_cache(cache)
        print(f"Saved cache ({total_updated} tracks updated so far)")
        
        # Rate limiting between batches
        time.sleep(1)
    
    # Save final cache state
    save_track_cache(cache)
    print(f"\nCache update complete. Updated {total_updated} tracks in total.")

if __name__ == "__main__":
    update_cache_for_all_artists() 