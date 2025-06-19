#!/usr/bin/env python3
"""
Add_Custom_Genres.py - Manually add custom genres for artists

This script allows you to:
1. Add custom genres for artists not in the cache
2. Update custom genres for existing artists
3. View current custom genres
4. Search for artists by name
"""

from typing import Dict, List, Any
from Artist_Genres import load_custom_genres, save_custom_genres
from spotify_client import sp

def normalize_genre_for_storage(genre: str) -> str:
    """Normalize genre for storage: lowercase and remove hyphens"""
    # Convert to lowercase
    normalized = genre.lower()
    # Remove hyphens and replace with spaces
    normalized = normalized.replace('-', ' ')
    # Remove extra spaces
    normalized = ' '.join(normalized.split())
    return normalized

def search_artist_by_name(artist_name: str) -> List[Dict[str, Any]]:
    """Search for an artist by name and return results"""
    try:
        results = sp.search(q=artist_name, type='artist', limit=10)
        return results['artists']['items']
    except Exception as e:
        print(f"Error searching for artist: {str(e)}")
        return []

def get_artist_by_id(artist_id: str) -> Dict[str, Any]:
    """Get artist details by ID"""
    try:
        return sp.artist(artist_id)
    except Exception as e:
        print(f"Error getting artist: {str(e)}")
        return {}

def add_artist_custom_genres(artist_id: str, artist_name: str, genres: List[str]) -> None:
    """Add or update custom genres for an artist"""
    # Load existing custom genres
    custom_genres = load_custom_genres()
    
    # Normalize genres
    normalized_genres = [normalize_genre_for_storage(genre) for genre in genres]
    # Remove duplicates while preserving order
    normalized_genres = list(dict.fromkeys(normalized_genres))
    
    # Add or update the artist
    custom_genres[artist_id] = {
        "name": artist_name,
        "genres": normalized_genres
    }
    
    # Save back to file
    save_custom_genres(custom_genres)
    
    print(f"✅ Added custom genres for {artist_name}: {', '.join(normalized_genres)}")

def view_custom_genres() -> None:
    """View all current custom genres"""
    custom_genres = load_custom_genres()
    
    if not custom_genres:
        print("❌ No custom genres found")
        return
    
    print("📊 Current Custom Genres:")
    print("=" * 60)
    
    for artist_id, artist_data in custom_genres.items():
        if isinstance(artist_data, dict) and 'name' in artist_data:
            name = artist_data['name']
            genres = artist_data.get('genres', [])
            print(f"🎤 {name} ({artist_id}): {', '.join(genres) if genres else 'No genres'}")

def search_and_add_artist() -> None:
    """Search for an artist and add custom genres"""
    print("\n🔍 Artist Search and Custom Genre Addition")
    print("=" * 60)
    
    # Get artist name from user
    artist_name = input("Enter artist name to search: ").strip()
    
    if not artist_name:
        print("❌ No artist name provided")
        return
    
    # Search for artist
    print(f"🔍 Searching for '{artist_name}'...")
    results = search_artist_by_name(artist_name)
    
    if not results:
        print("❌ No artists found")
        return
    
    # Show results
    print(f"\n📊 Found {len(results)} artists:")
    for i, artist in enumerate(results, 1):
        print(f"   {i}. {artist['name']} ({artist['id']})")
        if artist.get('genres'):
            print(f"      Current genres: {', '.join(artist['genres'])}")
        else:
            print(f"      No genres in Spotify")
    
    # Let user select
    try:
        choice = int(input(f"\nSelect artist (1-{len(results)}): ")) - 1
        if choice < 0 or choice >= len(results):
            print("❌ Invalid selection")
            return
        
        selected_artist = results[choice]
        artist_id = selected_artist['id']
        artist_name = selected_artist['name']
        
        print(f"\n🎤 Selected: {artist_name}")
        
        # Get custom genres from user
        genres_input = input("Enter custom genres (comma-separated): ").strip()
        if not genres_input:
            print("❌ No genres provided")
            return
        
        genres = [genre.strip() for genre in genres_input.split(',') if genre.strip()]
        
        # Add the custom genres
        add_artist_custom_genres(artist_id, artist_name, genres)
        
    except ValueError:
        print("❌ Invalid input")
        return

def add_by_artist_id() -> None:
    """Add custom genres by artist ID"""
    print("\n🆔 Add Custom Genres by Artist ID")
    print("=" * 60)
    
    artist_id = input("Enter artist ID: ").strip()
    if not artist_id:
        print("❌ No artist ID provided")
        return
    
    # Get artist details
    artist = get_artist_by_id(artist_id)
    if not artist:
        print("❌ Artist not found")
        return
    
    artist_name = artist['name']
    print(f"🎤 Found artist: {artist_name}")
    
    # Get custom genres from user
    genres_input = input("Enter custom genres (comma-separated): ").strip()
    if not genres_input:
        print("❌ No genres provided")
        return
    
    genres = [genre.strip() for genre in genres_input.split(',') if genre.strip()]
    
    # Add the custom genres
    add_artist_custom_genres(artist_id, artist_name, genres)

def remove_artist_custom_genres(artist_id: str) -> None:
    """Remove custom genres for an artist"""
    custom_genres = load_custom_genres()
    
    if artist_id in custom_genres:
        artist_name = custom_genres[artist_id].get('name', 'Unknown')
        del custom_genres[artist_id]
        save_custom_genres(custom_genres)
        print(f"✅ Removed custom genres for {artist_name}")
    else:
        print("❌ Artist not found in custom genres")

def main():
    """Main function"""
    print("🎵 Custom Genre Manager")
    print("=" * 60)
    
    while True:
        print("\nOptions:")
        print("1. View current custom genres")
        print("2. Search and add artist custom genres")
        print("3. Add custom genres by artist ID")
        print("4. Remove artist custom genres")
        print("5. Exit")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == '1':
            view_custom_genres()
        elif choice == '2':
            search_and_add_artist()
        elif choice == '3':
            add_by_artist_id()
        elif choice == '4':
            artist_id = input("Enter artist ID to remove: ").strip()
            if artist_id:
                remove_artist_custom_genres(artist_id)
        elif choice == '5':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid option")

if __name__ == "__main__":
    main() 