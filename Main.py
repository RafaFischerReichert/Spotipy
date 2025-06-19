#!/usr/bin/env python3
"""
Main.py - Orchestrates the entire genre playlist creation process

This script:
1. Checks for artists without genres in the cache
2. Populates custom genres using Wikipedia API
3. Creates genre playlists from the source playlist
4. Handles all the necessary caching and optimization
"""

import os
import sys
import time
from config import PLAYLIST_ID, REQUESTS_PER_SECOND

# Import all necessary modules
from List_Empty_Cache import list_artists_without_genres
from WikipediaGenres import main as populate_custom_genres
from Playlist_Creator import create_genre_playlists_optimized
from Genre_Tools import load_artist_cache, save_artist_cache
from Artist_Genres import load_custom_genres

def update_artist_cache_with_custom_genres() -> None:
    """Update the artist cache with custom genres from the JSON file"""
    print("🔄 Updating artist cache with custom genres...")
    
    # Load existing cache
    artist_cache = load_artist_cache()
    
    # Load custom genres
    custom_genres = load_custom_genres()
    
    if not custom_genres:
        print("⚠️  No custom genres found to update cache.")
        return
    
    updated_count = 0
    artists_still_empty = 0
    
    # Update cache with custom genres
    for artist_id, custom_genre_list in custom_genres.items():
        if artist_id in artist_cache:
            # Add custom genres to existing genres
            artist_cache[artist_id]['genres'].extend(custom_genre_list)
            # Remove duplicates while preserving order
            artist_cache[artist_id]['genres'] = list(dict.fromkeys(artist_cache[artist_id]['genres']))
            updated_count += 1
        else:
            # Create new entry with custom genres
            artist_cache[artist_id] = {
                'genres': custom_genre_list,
                'country': None
            }
            updated_count += 1
    
    # Save updated cache
    save_artist_cache(artist_cache)
    
    print(f"✅ Updated {updated_count} artists with custom genres")
    print(f"⚠️  {artists_still_empty} artists still have no genres")
    
    return updated_count, artists_still_empty

def check_artists_without_genres() -> bool:
    """Check if there are artists without genres and generate the list if needed"""
    print("=" * 60)
    print("STEP 1: Checking for artists without genres...")
    print("=" * 60)
    
    # Load existing cache
    artist_cache = load_artist_cache()
    
    # Count artists with and without genres
    artists_with_genres = sum(1 for data in artist_cache.values() if data['genres'])
    artists_without_genres = sum(1 for data in artist_cache.values() if not data['genres'])
    
    if not artists_without_genres:
        print("✅ No artists without genres found in cache.")
        return False
    
    print(f"⚠️  Found {artists_without_genres} artists without genres.")
    print("Generating list of artists without genres...")
    
    # Generate the list
    list_artists_without_genres()
    
    # Check if the JSON file was created
    if os.path.exists('artists_without_genres.json'):
        print("✅ Successfully generated artists_without_genres.json")
        return True
    else:
        print("❌ Failed to generate artists_without_genres.json")
        return False

def populate_custom_genres_if_needed() -> bool:
    """Populate custom genres using Wikipedia API if needed"""
    print("\n" + "=" * 60)
    print("STEP 2: Checking for custom genres...")
    print("=" * 60)
    
    # Check if custom genres file exists
    if os.path.exists('custom_artist_genres.json'):
        custom_genres = load_custom_genres()
        if custom_genres:
            print(f"✅ Custom genres file exists with {len(custom_genres)} artists.")
            # Update cache with existing custom genres
            update_artist_cache_with_custom_genres()
            return True
    
    # Check if we have artists without genres to process
    if not os.path.exists('artists_without_genres.json'):
        print("✅ No artists without genres to process.")
        return True
    
    print("⚠️  Custom genres not found. Populating from Wikipedia...")
    
    try:
        populate_custom_genres()
        
        # Verify the file was created
        if os.path.exists('custom_artist_genres.json'):
            custom_genres = load_custom_genres()
            artists_with_genres = sum(1 for data in custom_genres.values() if data.get('genres'))
            print(f"✅ Successfully populated custom genres for {artists_with_genres} artists.")
            
            # Update artist cache with the new custom genres
            update_artist_cache_with_custom_genres()
            
            return True
        else:
            print("❌ Failed to create custom_artist_genres.json")
            return False
            
    except Exception as e:
        print(f"❌ Error populating custom genres: {str(e)}")
        return False

def create_genre_playlists() -> bool:
    """Create genre playlists from the source playlist"""
    print("\n" + "=" * 60)
    print("STEP 3: Creating genre playlists...")
    print("=" * 60)
    
    try:
        print(f"🎵 Creating genre playlists from playlist ID: {PLAYLIST_ID}")
        create_genre_playlists_optimized(PLAYLIST_ID)
        print("✅ Successfully created genre playlists!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating genre playlists: {str(e)}")
        return False

def print_summary():
    """Print a summary of the current state"""
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    # Artist cache stats
    artist_cache = load_artist_cache()
    artists_with_genres = sum(1 for data in artist_cache.values() if data['genres'])
    artists_without_genres = sum(1 for data in artist_cache.values() if not data['genres'])
    
    print(f"📊 Artist Cache:")
    print(f"   - Total artists: {len(artist_cache)}")
    print(f"   - Artists with genres: {artists_with_genres}")
    print(f"   - Artists without genres: {artists_without_genres}")
    
    # Custom genres stats
    if os.path.exists('custom_artist_genres.json'):
        custom_genres = load_custom_genres()
        artists_with_custom_genres = sum(1 for data in custom_genres.values() if data.get('genres'))
        print(f"📊 Custom Genres:")
        print(f"   - Total artists with custom genres: {len(custom_genres)}")
        print(f"   - Artists with populated genres: {artists_with_custom_genres}")
    
    # Playlist stats
    try:
        from Playlist_Tools import get_existing_playlists
        existing_playlists = get_existing_playlists()
        genre_playlists = [name for name in existing_playlists.keys() if any(genre in name.lower() for genre in ['rock', 'pop', 'hip hop', 'metal', 'jazz', 'classical', 'electronic', 'folk', 'country', 'r&b', 'blues', 'reggae', 'punk', 'indie', 'alternative', 'brazilian', 'japanese'])]
        print(f"📊 Playlists:")
        print(f"   - Total playlists: {len(existing_playlists)}")
        print(f"   - Genre playlists: {len(genre_playlists)}")
    except Exception as e:
        print(f"📊 Playlists: Unable to fetch playlist stats ({str(e)})")

def main():
    """Main orchestration function"""
    print("🎵 Spotify Genre Playlist Creator")
    print("=" * 60)
    print(f"Source Playlist ID: {PLAYLIST_ID}")
    print(f"Rate Limit: {REQUESTS_PER_SECOND} requests/second")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # Step 1: Check for artists without genres
        has_artists_without_genres = check_artists_without_genres()
        
        # Step 2: Populate custom genres if needed
        if has_artists_without_genres:
            success = populate_custom_genres_if_needed()
            if not success:
                print("⚠️  Warning: Failed to populate custom genres, but continuing...")
        
        # Step 3: Create genre playlists
        success = create_genre_playlists()
        if not success:
            print("❌ Failed to create genre playlists.")
            return False
        
        # Print summary
        print_summary()
        
        elapsed_time = time.time() - start_time
        print(f"\n⏱️  Total execution time: {elapsed_time:.2f} seconds")
        print("🎉 Process completed successfully!")
        
        return True
        
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user.")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 