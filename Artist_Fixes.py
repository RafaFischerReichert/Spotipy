# ---
# Artist_Fixes.py
# Fixes the artist cache by applying custom genre mappings to artists with empty genre arrays.
# Provides statistics on the cache before and after fixing, and saves the updated cache.
# ---
import json
import os
from Artist_Genres import get_custom_artist_genres

def fix_artist_cache():
    """
    Fix the artist cache by applying custom genre mappings from Artist_Genres.py
    to artists that currently have empty genre arrays.
    """
    # Load the current artist cache
    cache_file = "artist_genre_cache.json"
    
    if not os.path.exists(cache_file):
        print(f"Cache file {cache_file} not found!")
        return
    
    print("Loading current artist cache...")
    with open(cache_file, 'r', encoding='utf-8') as f:
        artist_cache = json.load(f)
    
    print(f"Loaded {len(artist_cache)} artists from cache")
    
    # Count artists with empty genres
    empty_genre_count = sum(1 for data in artist_cache.values() if not data['genres'])
    print(f"Found {empty_genre_count} artists with empty genres")
    
    # Apply custom genre mappings
    fixed_count = 0
    updated_artists = []
    
    for artist_id, data in artist_cache.items():
        if not data['genres']:
            custom_genres = get_custom_artist_genres(artist_id)
            if custom_genres:
                artist_cache[artist_id]['genres'] = custom_genres
                fixed_count += 1
                updated_artists.append(artist_id)
                print(f"Fixed artist {artist_id}: {custom_genres}")
    
    print(f"\nFixed {fixed_count} artists with custom genre mappings")
    
    if fixed_count > 0:
        # Save the updated cache
        print("Saving updated artist cache...")
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(artist_cache, f, ensure_ascii=False, indent=2)
        print("Artist cache updated successfully!")
        
        # Show some examples of fixed artists
        print(f"\nExamples of fixed artists:")
        for artist_id in updated_artists[:10]:  # Show first 10
            print(f"  {artist_id}: {artist_cache[artist_id]['genres']}")
        
        if len(updated_artists) > 10:
            print(f"  ... and {len(updated_artists) - 10} more")
    else:
        print("No artists needed fixing!")

def show_cache_stats():
    """Show statistics about the current artist cache."""
    cache_file = "artist_genre_cache.json"
    
    if not os.path.exists(cache_file):
        print(f"Cache file {cache_file} not found!")
        return
    
    with open(cache_file, 'r', encoding='utf-8') as f:
        artist_cache = json.load(f)
    
    total_artists = len(artist_cache)
    empty_genre_count = sum(1 for data in artist_cache.values() if not data['genres'])
    artists_with_genres = total_artists - empty_genre_count
    
    print(f"Artist Cache Statistics:")
    print(f"  Total artists: {total_artists}")
    print(f"  Artists with genres: {artists_with_genres}")
    print(f"  Artists without genres: {empty_genre_count}")
    print(f"  Percentage with genres: {(artists_with_genres/total_artists)*100:.1f}%")

if __name__ == "__main__":
    print("Artist Cache Fixer")
    print("=" * 50)
    
    # Show current stats
    show_cache_stats()
    print()
    
    # Fix the cache
    fix_artist_cache()
    print()
    
    # Show updated stats
    show_cache_stats()
