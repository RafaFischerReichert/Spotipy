import time
from typing import Dict, List, Set, Any
from spotify_client import sp
from Genre_Tools import load_artist_cache, normalize_genre
from Playlist_Tools import get_playlist_tracks, get_existing_playlists, get_playlist_track_ids, RateLimiter
from config import PLAYLIST_ID, REQUESTS_PER_SECOND
from tqdm import tqdm

def get_brazilian_artists() -> Set[str]:
    """Get all Brazilian artist IDs from the cache"""
    artist_cache = load_artist_cache()
    brazilian_artists = set()
    
    for artist_id, data in artist_cache.items():
        # Check if artist has Brazilian genres
        genres = data.get('genres', [])
        for genre in genres:
            normalized_genres = normalize_genre(genre)
            if 'Brazilian Music' in normalized_genres or 'brazilian music' in normalized_genres:
                brazilian_artists.add(artist_id)
                break
        
        # Also check country from Wikipedia
        country = data.get('country')
        if country and 'Brazil' in country:
            brazilian_artists.add(artist_id)
    
    return brazilian_artists

def get_tracks_by_artists(playlist_id: str, artist_ids: Set[str]) -> Set[str]:
    """Get all track IDs from a playlist that are by the specified artists"""
    tracks = get_playlist_tracks(playlist_id)
    matching_track_ids = set()
    
    print(f"Scanning {len(tracks)} tracks for Brazilian artists...")
    
    for track in tqdm(tracks, desc="Finding Brazilian tracks"):
        if track['track']:
            track_artists = [artist['id'] for artist in track['track']['artists']]
            # If any artist on the track is Brazilian, include the track
            if any(artist_id in artist_ids for artist_id in track_artists):
                matching_track_ids.add(track['track']['id'])
    
    return matching_track_ids

def add_tracks_to_playlist(playlist_id: str, track_ids: Set[str], rate_limiter: RateLimiter) -> int:
    """Add tracks to playlist in batches, skipping existing tracks"""
    if not track_ids:
        return 0
    
    # Get existing tracks in playlist
    existing_tracks = get_playlist_track_ids(playlist_id)
    
    # Filter out tracks that already exist
    new_track_ids = track_ids - existing_tracks
    
    if not new_track_ids:
        print("All tracks already exist in the playlist!")
        return 0
    
    print(f"Adding {len(new_track_ids)} new tracks to playlist...")
    
    # Add tracks in batches of 50
    track_ids_list = list(new_track_ids)
    added_count = 0
    
    for i in tqdm(range(0, len(track_ids_list), 50), desc="Adding tracks"):
        batch = track_ids_list[i:i + 50]
        try:
            sp.playlist_add_items(playlist_id, batch)
            added_count += len(batch)
            rate_limiter.wait()
        except Exception as e:
            print(f"Error adding batch {i//50 + 1}: {str(e)}")
            # Try individual tracks
            for track_id in batch:
                try:
                    sp.playlist_add_items(playlist_id, [track_id])
                    added_count += 1
                    rate_limiter.wait()
                except Exception as e2:
                    print(f"Error adding track {track_id}: {str(e2)}")
                    continue
    
    return added_count

def main():
    """Main function to add Brazilian songs to Brazilian Music playlist"""
    print("🎵 Adding Brazilian songs to Brazilian Music playlist")
    print("=" * 60)
    
    # Initialize rate limiter
    rate_limiter = RateLimiter(requests_per_second=REQUESTS_PER_SECOND)
    
    # Get Brazilian artists
    print("Finding Brazilian artists in cache...")
    brazilian_artists = get_brazilian_artists()
    print(f"Found {len(brazilian_artists)} Brazilian artists")
    
    if not brazilian_artists:
        print("No Brazilian artists found in cache!")
        return
    
    # Get Brazilian tracks from source playlist
    print(f"Finding tracks by Brazilian artists in playlist {PLAYLIST_ID}...")
    brazilian_tracks = get_tracks_by_artists(PLAYLIST_ID, brazilian_artists)
    print(f"Found {len(brazilian_tracks)} tracks by Brazilian artists")
    
    if not brazilian_tracks:
        print("No Brazilian tracks found in source playlist!")
        return
    
    # Get existing playlists
    existing_playlists = get_existing_playlists()
    
    # Find Brazilian Music playlist
    brazilian_playlist_id = None
    for name, playlist_id in existing_playlists.items():
        if name.lower() == 'brazilian music':
            brazilian_playlist_id = playlist_id
            break
    
    if not brazilian_playlist_id:
        print("Brazilian Music playlist not found!")
        print("Available playlists:")
        for name in existing_playlists.keys():
            if 'brazilian' in name.lower():
                print(f"  - {name}")
        return
    
    print(f"Found Brazilian Music playlist: {brazilian_playlist_id}")
    
    # Add tracks to playlist
    start_time = time.time()
    added_count = add_tracks_to_playlist(brazilian_playlist_id, brazilian_tracks, rate_limiter)
    elapsed_time = time.time() - start_time
    
    print(f"\n✅ Successfully added {added_count} tracks to Brazilian Music playlist")
    print(f"⏱️  Time elapsed: {elapsed_time:.2f} seconds")
    
    # Show final playlist stats
    final_track_count = len(get_playlist_track_ids(brazilian_playlist_id))
    print(f"📊 Brazilian Music playlist now has {final_track_count} tracks")

if __name__ == "__main__":
    main() 