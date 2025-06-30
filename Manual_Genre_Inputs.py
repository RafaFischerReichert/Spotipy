"""Allows manual input of genres for artists missing genre data in the cache.

This module allows manual input of genres for artists missing genre data in the 
cache. Prompts the user for genres, normalizes and deduplicates them, and 
updates the cache.
"""

import json
import os
from typing import Dict, List, Set, Optional, Any
from Genre_Tools import load_artist_cache, save_artist_cache, get_artist_genres, normalize_genre, deduplicate_hyphen_genres, get_artist_name_from_cache

def get_artists_without_genres(artist_cache: Dict[str, Dict[str, Any]]) -> List[str]:
    """Get list of artist IDs that have no genres or only have generic regional genres in cache.
    
    Args:
        artist_cache: The artist cache dictionary to check.
        
    Returns:
        List of artist IDs that have no genres or only have generic regional genres.
    """
    artists_without_genres = []
    generic_regional_genres = {"brazilian music", "japanese music"}
    
    for artist_id, data in artist_cache.items():
        genres = data.get('genres', [])
        if not genres:
            artists_without_genres.append(artist_id)
        elif len(genres) == 1 and genres[0].lower() in generic_regional_genres:
            artists_without_genres.append(artist_id)
    
    return artists_without_genres

def manual_genre_input():
    """Allow manual input of genres for artists that don't have them or have generic regional genres."""
    print("\n=== Manual Genre Input Tool ===\n")
    
    # Load existing cache
    print("Loading artist cache...")
    artist_cache = load_artist_cache()
    print(f"Loaded {len(artist_cache)} artists from cache")
    
    # Find artists without genres or with generic regional genres
    artists_without_genres = get_artists_without_genres(artist_cache)
    print(f"Found {len(artists_without_genres)} artists without genres or with generic regional genres")
    
    if not artists_without_genres:
        print("✅ All artists already have proper genres!")
        return
    
    print(f"\nYou will be prompted to enter genres for {len(artists_without_genres)} artists.")
    print("This includes artists with no genres and artists with only 'Brazilian Music' or 'Japanese Music'")
    print("Enter genres separated by commas (e.g., 'rock, alternative, indie')")
    print("Press Enter to skip an artist, 'quit' to exit early\n")
    
    processed = 0
    skipped = 0
    
    for i, artist_id in enumerate(artists_without_genres, 1):
        artist_name = get_artist_name_from_cache(artist_id, artist_cache)
        current_genres = artist_cache.get(artist_id, {}).get('genres', [])
        
        print(f"\n[{i}/{len(artists_without_genres)}] Artist: {artist_name}")
        print(f"Spotify ID: {artist_id}")
        if current_genres:
            print(f"Current genres: {', '.join(current_genres)}")
        else:
            print("Current genres: None")
        
        while True:
            genres_input = input("Enter genres (comma-separated): ").strip()
            
            if genres_input.lower() == 'quit':
                print(f"\nExiting early. Processed: {processed}, Skipped: {skipped}")
                return
            
            if not genres_input:
                print("Skipping this artist...")
                skipped += 1
                break
            
            # Parse genres
            genres = [g.strip() for g in genres_input.split(',') if g.strip()]
            
            if not genres:
                print("No valid genres entered. Please try again or press Enter to skip.")
                continue
            
            # Normalize genres
            normalized_genres = []
            for genre in genres:
                normalized = normalize_genre(genre)
                normalized_genres.extend(normalized)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_normalized_genres = []
            for genre in normalized_genres:
                if genre not in seen:
                    seen.add(genre)
                    unique_normalized_genres.append(genre)
            
            # Deduplicate hyphen genres
            unique_normalized_genres = deduplicate_hyphen_genres(unique_normalized_genres)
            
            # Update cache
            if artist_id not in artist_cache:
                artist_cache[artist_id] = {}
            
            artist_cache[artist_id]['genres'] = unique_normalized_genres
            processed += 1
            
            print(f"✅ Added normalized genres: {', '.join(unique_normalized_genres)}")
            break
    
    # Save updated cache
    print(f"\nSaving updated cache...")
    save_artist_cache(artist_cache)
    
    print(f"\n=== Manual Genre Input Complete ===")
    print(f"Artists processed: {processed}")
    print(f"Artists skipped: {skipped}")
    print(f"Total artists in cache: {len(artist_cache)}")

if __name__ == "__main__":
    manual_genre_input()
