#!/usr/bin/env python3
# ---
# Main.py
# Orchestrates the entire genre playlist creation process.
# Creates genre playlists, manages caching, and prints summary statistics for artists and playlists.
# ---

import os
import sys
import time
from config import PLAYLIST_ID, REQUESTS_PER_SECOND

# Import all necessary modules
from Playlist_Creator import create_genre_playlists_optimized
from Genre_Tools import load_artist_cache
from Artist_Genres import load_custom_genres

def create_genre_playlists() -> bool:
    """Create genre playlists from the source playlist"""
    print("=" * 60)
    print("Creating genre playlists...")
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
        # Create genre playlists
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