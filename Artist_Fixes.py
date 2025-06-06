from typing import List, Dict, Any
import json
import os
import time
from spotify_client import sp, get_artist_with_retry
from Genre_Tools import get_track_genres, load_track_cache, save_track_cache
from Artist_Genres import get_custom_artist_genres

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

def get_artist_tracks(artist_id: str) -> List[Dict[str, Any]]:
    """Get all tracks by an artist from their albums."""
    tracks = []
    try:
        albums = sp.artist_albums(artist_id, album_type='album,single', limit=50)
        
        for album in albums['items']:
            album_tracks = sp.album_tracks(album['id'])
            for track in album_tracks['items']:
                if any(artist['id'] == artist_id for artist in track['artists']):
                    tracks.append({'track': track})  # Wrap in same format as playlist tracks
            time.sleep(0.1)  # Rate limiting
        time.sleep(0.2)  # Rate limiting between albums
    except Exception as e:
        print(f"Error getting tracks for artist {artist_id}: {str(e)}")
    return tracks

def update_cache_for_all_artists() -> None:
    """Update the cache for all artists in the genre mappings."""
    # Load current cache
    cache = load_track_cache()
    artist_cache = {}  # Cache for artist data
    total_updated = 0
    
    # Get all artist IDs from the mappings
    from Artist_Genres import ARTIST_GENRE_MAPPINGS
    artist_ids = list(ARTIST_GENRE_MAPPINGS.keys())
    
    print(f"\nUpdating cache for {len(artist_ids)} artists...")
    
    for i, artist_id in enumerate(artist_ids, 1):
        try:
            artist = get_artist_with_retry(artist_id)
            artist_name = artist['name']
            print(f"\nProcessing {i}/{len(artist_ids)}: {artist_name}")
            
            # Get all tracks for this artist
            tracks = get_artist_tracks(artist_id)
            print(f"Found {len(tracks)} tracks")
            
            # Update cache for each track
            for track in tracks:
                if not track['track']:
                    continue
                    
                track_id = track['track']['id']
                # Get genres using our custom function
                genres = get_track_genres(track, artist_cache)
                if genres:  # Only update if we got genres
                    cache[track_id] = genres
                    total_updated += 1
            
            # Save cache periodically
            if i % 5 == 0:
                save_track_cache(cache)
                print(f"Saved cache ({total_updated} tracks updated so far)")
            
        except Exception as e:
            print(f"Error processing artist {artist_id}: {str(e)}")
            continue
    
    # Save final cache state
    save_track_cache(cache)
    print(f"\nCache update complete. Updated {total_updated} tracks in total.")

if __name__ == "__main__":
    update_cache_for_all_artists() 