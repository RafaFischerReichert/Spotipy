# ---
# Playlist_Creator.py
# Creates genre playlists from a source playlist, using optimized batch processing and caching.
# Minimizes API calls and speeds up playlist creation by batching and checking for existing playlists.
# ---
import time
from typing import Dict, List, Set, Any
from config import PLAYLIST_ID, REQUESTS_PER_SECOND
from Playlist_Tools import (
    get_existing_playlists,
    get_playlist_track_ids,
    create_genre_playlists,
    sp,
    RateLimiter
)

def create_genre_playlists_optimized(playlist_id: str) -> None:
    """Create genre playlists with optimized batch processing and caching"""
    # Initialize rate limiter using config value
    rate_limiter = RateLimiter(requests_per_second=REQUESTS_PER_SECOND)
    
    # Use the optimized function from Playlist_Tools
    genre_tracks = create_genre_playlists(playlist_id)
    
    # Get user's playlists to check for existing ones
    existing_playlists: Dict[str, str] = get_existing_playlists()
    
    # Batch create playlists and add tracks
    playlists_to_create = []
    playlists_to_update = []
    
    for genre, track_ids in genre_tracks.items():
        if len(track_ids) < 100:  # Skip genres with too few tracks
            continue
            
        playlist_name: str = f"{genre.title()}"
        
        if playlist_name in existing_playlists:
            playlists_to_update.append((playlist_name, existing_playlists[playlist_name], track_ids))
        else:
            playlists_to_create.append((playlist_name, track_ids))
    
    # Create new playlists in batches
    if playlists_to_create:
        print(f"\nCreating {len(playlists_to_create)} new playlists...")
        user_id = sp.current_user()['id']
        
        for playlist_name, track_ids in playlists_to_create:
            try:
                playlist: Dict[str, Any] = sp.user_playlist_create(
                    user=user_id,
                    name=playlist_name,
                    public=True
                )
                playlist_id: str = playlist['id']
                print(f"Created new playlist '{playlist_name}'")
                
                # Add tracks to playlist in chunks of 50
                track_ids_list: List[str] = list(track_ids)
                for i in range(0, len(track_ids_list), 50):
                    chunk: List[str] = track_ids_list[i:i + 50]
                    sp.playlist_add_items(playlist_id, chunk)
                    rate_limiter.wait()
                
                print(f"Added {len(track_ids)} tracks to '{playlist_name}'")
                rate_limiter.wait()
                
            except Exception as e:
                print(f"Error creating playlist for {genre}: {str(e)}")
                time.sleep(5)  # Long delay after error
                continue
    
    # Update existing playlists in batches
    if playlists_to_update:
        print(f"\nUpdating {len(playlists_to_update)} existing playlists...")
        
        for playlist_name, playlist_id, track_ids in playlists_to_update:
            try:
                print(f"Checking existing tracks in '{playlist_name}'...")
                
                # Get existing tracks in playlist
                existing_tracks: Set[str] = get_playlist_track_ids(playlist_id)
                
                # Filter out tracks that already exist in the playlist
                new_track_ids = track_ids - existing_tracks
                
                if new_track_ids:
                    print(f"Adding {len(new_track_ids)} new tracks to '{playlist_name}'...")
                    
                    # Add tracks to playlist in chunks of 50
                    track_ids_list: List[str] = list(new_track_ids)
                    for i in range(0, len(track_ids_list), 50):
                        chunk: List[str] = track_ids_list[i:i + 50]
                        sp.playlist_add_items(playlist_id, chunk)
                        rate_limiter.wait()
                    
                    print(f"Added {len(new_track_ids)} tracks to '{playlist_name}'")
                else:
                    print(f"No new tracks to add to '{playlist_name}'")
                
            except Exception as e:
                print(f"Error updating playlist for {genre}: {str(e)}")
                time.sleep(5)  # Long delay after error
                continue

if __name__ == "__main__":
    create_genre_playlists_optimized(PLAYLIST_ID)