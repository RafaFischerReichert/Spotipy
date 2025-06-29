"""Lists all unique genres found in a playlist.

This module lists all unique genres found in a playlist, using batch processing 
and normalization for efficiency and accuracy. Prints the total number of 
unique genres found.
"""

from typing import Dict, List, Set, Any
from config import REQUESTS_PER_SECOND
from Playlist_Tools import (
    get_playlist_tracks,
    get_track_genres,
    sp,
    RateLimiter
)
from Genre_Tools import load_artist_cache, normalize_genre

def list_playlist_genres(playlist_id: str) -> None:
    """List all unique genres found in a playlist with optimized batch processing.
    
    Args:
        playlist_id: The Spotify playlist ID to analyze for genres.
    """
    # Initialize rate limiter
    rate_limiter = RateLimiter(requests_per_second=REQUESTS_PER_SECOND)
    
    # Get all tracks from the playlist
    tracks: List[Dict[str, Any]] = get_playlist_tracks(playlist_id)
    
    # Load artist cache for better performance
    artist_cache: Dict[str, Dict[str, Any]] = load_artist_cache()
    
    # Process tracks with pre-loaded cache
    print(f"Processing {len(tracks)} tracks with pre-loaded artist cache...")

    track_genres_map: Dict[str, List[str]] = {}
    # Step 1: Collect raw genres for all tracks
    for track in tracks:
        if track and track['track']:
            track_id = track['track']['id']
            raw_genres = get_track_genres(track, artist_cache)
            track_genres_map[track_id] = raw_genres

    # Step 2: Create a normalization map for all unique raw genres
    all_raw_genres = set(g for genres in track_genres_map.values() for g in genres)
    normalization_map = {genre: normalize_genre(genre) for genre in all_raw_genres}

    # Step 3: Collect all unique normalized genres using the map
    unique_normalized_genres: Set[str] = set()
    for raw_genres in track_genres_map.values():
        for raw_genre in raw_genres:
            normalized_genres = normalization_map.get(raw_genre, [])
            unique_normalized_genres.update(normalized_genres)
    
    # Print results
    print("\nUnique genres found in playlist:")
    for genre in sorted(unique_normalized_genres):
        print(f"- {genre}")
    print(f"\nTotal unique genres: {len(unique_normalized_genres)}")

if __name__ == "__main__":
    from config import PLAYLIST_ID
    list_playlist_genres(PLAYLIST_ID)
