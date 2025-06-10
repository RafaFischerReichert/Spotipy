from collections import defaultdict
import time
from typing import Dict, List, Any
from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, REQUESTS_PER_SECOND
from Playlist_Tools import (
    get_playlist_tracks,
    get_track_genres,
    sp,
    RateLimiter
)
from Genre_Tools import load_artist_cache

def rank_playlist_genres(playlist_id: str) -> None:
    """List genres found in a playlist, ranked by frequency"""
    # Initialize rate limiter
    rate_limiter = RateLimiter(requests_per_second=REQUESTS_PER_SECOND)
    
    # Get all tracks from the playlist
    tracks: List[Dict[str, Any]] = get_playlist_tracks(playlist_id)
    
    # Dictionary to store genre counts
    genre_counts: Dict[str, int] = defaultdict(int)
    
    # Load artist cache
    artist_cache: Dict[str, List[str]] = load_artist_cache()
    
    # Process tracks
    for i, track in enumerate(tracks):
        if i % 50 == 0:
            print(f"Processing track {i}/{len(tracks)}")
        
        genres: List[str] = get_track_genres(track, artist_cache)
        for genre in genres:
            genre_counts[genre] += 1
        rate_limiter.wait()
    
    # Sort genres by count (descending)
    sorted_genres: List[tuple[str, int]] = sorted(
        genre_counts.items(),
        key=lambda x: (-x[1], x[0])  # Sort by count (descending) then alphabetically
    )
    
    # Print results
    print("\nGenres ranked by frequency:")
    for genre, count in sorted_genres:
        percentage: float = (count / len(tracks)) * 100
        print(f"- {genre}: {count} tracks ({percentage:.1f}%)")
    print(f"\nTotal unique genres: {len(genre_counts)}")

if __name__ == "__main__":
    from config import PLAYLIST_ID
    rank_playlist_genres(PLAYLIST_ID) 