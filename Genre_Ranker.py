from collections import defaultdict
from typing import Dict, List, Any, Set
from config import REQUESTS_PER_SECOND
from Playlist_Tools import (
    get_playlist_tracks,
    get_track_genres,
    sp,
    RateLimiter
)
from Genre_Tools import load_artist_cache, get_custom_artist_genres
from WikipediaAPI import get_artist_country_wikidata


def rank_playlist_genres(playlist_id: str) -> None:
    """List genres found in a playlist, ranked by frequency with optimized batch processing"""
    # Initialize rate limiter
    rate_limiter = RateLimiter(requests_per_second=REQUESTS_PER_SECOND)
    
    # Get all tracks from the playlist
    tracks: List[Dict[str, Any]] = get_playlist_tracks(playlist_id)
    
    # Dictionary to store genre counts
    genre_counts: Dict[str, int] = defaultdict(int)
    
    # Load artist cache for better performance
    artist_cache: Dict[str, Dict[str, Any]] = load_artist_cache()
    
    # Extract all unique artist IDs from tracks for batch processing
    all_artist_ids: Set[str] = set()
    for track in tracks:
        if track['track']:
            for artist in track['track']['artists']:
                all_artist_ids.add(artist['id'])
    
    # Pre-load uncached artists in batches
    uncached_artist_ids = [aid for aid in all_artist_ids if aid not in artist_cache]
    if uncached_artist_ids:
        print(f"Pre-loading {len(uncached_artist_ids)} uncached artists...")
        
        for i in range(0, len(uncached_artist_ids), 50):
            batch_artist_ids = uncached_artist_ids[i:i + 50]
            try:
                artists = sp.artists(batch_artist_ids)
                
                for artist in artists['artists']:
                    if artist:  # Check if artist exists
                        artist_id = artist['id']
                        genres = artist['genres']
                        
                        # Add custom genres if available
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
                continue
    
    # Process tracks with pre-loaded cache
    print(f"Processing {len(tracks)} tracks with pre-loaded artist cache...")
    for i, track in enumerate(tracks):
        if i % 100 == 0:
            print(f"Processing track {i}/{len(tracks)}")
        
        genres: List[str] = get_track_genres(track, artist_cache)
        for genre in genres:
            genre_counts[genre] += 1
    
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