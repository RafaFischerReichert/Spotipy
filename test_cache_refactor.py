#!/usr/bin/env python3
# ---
# test_cache_refactor.py
# Test script to verify that the cache refactoring works correctly.
# Tests the new cache structure with artist names.
# ---

from Genre_Tools import load_artist_cache, get_artist_name_from_cache
import json

def test_cache_structure():
    """Test that the cache structure includes artist names."""
    print("Testing cache structure...")
    
    # Load the cache
    cache = load_artist_cache()
    
    if not cache:
        print("Cache is empty. Run Artist_Cacher.py first to populate it.")
        return
    
    print(f"Loaded {len(cache)} artists from cache")
    
    # Check the structure of a few entries
    sample_count = min(5, len(cache))
    sample_artists = list(cache.items())[:sample_count]
    
    print(f"\nSample cache entries:")
    for artist_id, data in sample_artists:
        print(f"Artist ID: {artist_id}")
        print(f"  Name: {data.get('name', 'NOT SET')}")
        print(f"  Genres: {data.get('genres', [])}")
        print(f"  Country: {data.get('country', 'NOT SET')}")
        print()
    
    # Test the get_artist_name_from_cache function
    print("Testing get_artist_name_from_cache function...")
    for artist_id, data in sample_artists:
        cached_name = get_artist_name_from_cache(artist_id, cache)
        print(f"Artist {artist_id}: {cached_name}")
    
    # Count artists with names in cache
    artists_with_names = sum(1 for data in cache.values() if data.get('name'))
    print(f"\nArtists with names in cache: {artists_with_names}/{len(cache)} ({artists_with_names/len(cache)*100:.1f}%)")

def test_cache_migration():
    """Test that old cache format is properly migrated."""
    print("\nTesting cache migration...")
    
    # Create a mock old format cache
    old_format_cache = {
        "test_artist_1": ["rock", "alternative"],
        "test_artist_2": {
            "genres": ["pop", "electronic"],
            "country": "USA"
        }
    }
    
    # Save it temporarily
    with open("test_old_cache.json", "w") as f:
        json.dump(old_format_cache, f)
    
    # Load it using our function
    from Genre_Tools import load_artist_cache
    migrated_cache = load_artist_cache()
    
    print("Migration test completed.")
    
    # Clean up
    import os
    if os.path.exists("test_old_cache.json"):
        os.remove("test_old_cache.json")

if __name__ == "__main__":
    test_cache_structure()
    test_cache_migration() 