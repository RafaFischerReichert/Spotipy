# ---
# Artist_Checker.py
# Provides a menu-driven tool to check artist IDs, genres, and update the artist cache.
# Allows searching for artists by name or URL, viewing genres, and entering genres manually if missing.
# ---
import re
from typing import Dict, List, Any
from Playlist_Tools import sp
from spotify_client import get_artist_with_retry
from Genre_Tools import load_artist_cache, save_artist_cache, get_artist_name_from_cache

# Cache file path
ARTIST_CACHE_FILE = "artist_genre_cache.json"

def extract_artist_id_from_url(url: str) -> str:
    """Extract artist ID from Spotify artist URL."""
    # Remove everything after ?si= if present
    if '?si=' in url:
        url = url.split('?si=')[0]
    
    # Pattern to match artist ID in Spotify URLs
    pattern = r'/artist/([a-zA-Z0-9]+)'
    match = re.search(pattern, url)
    
    if match:
        return match.group(1)
    else:
        raise ValueError("Could not extract artist ID from the provided URL")

def update_tracks_for_artist(artist_id: str, artist_genres: List[str], cache: Dict[str, Dict[str, Any]]) -> None:
    """Update the cache for an artist with their genres."""
    # Get artist name from cache or API
    artist_name = get_artist_name_from_cache(artist_id, cache)
    
    # Update artist cache with name and genres
    cache[artist_id] = {
        'name': artist_name,
        'genres': artist_genres,
        'country': cache.get(artist_id, {}).get('country')
    }
    save_artist_cache(cache)
    print(f"\nUpdated cache for artist {artist_name} ({artist_id})")

def print_artist_genres(artist_id: str):
    """Print all genres for a given artist and update artist cache"""
    try:
        # Load current cache
        cache = load_artist_cache()
        
        # Try to get artist name from cache first
        artist_name = get_artist_name_from_cache(artist_id, cache)
        
        # Get artist data from API if not in cache
        if artist_id not in cache or not cache[artist_id].get('genres'):
            artist = get_artist_with_retry(artist_id)
            artist_name = artist['name']
            
            # Update cache with artist data
            cache[artist_id] = {
                'name': artist_name,
                'genres': artist.get('genres', []),
                'country': cache.get(artist_id, {}).get('country')
            }
            save_artist_cache(cache)
        
        print(f"\nGenres for {artist_name}:")
        
        genres = cache[artist_id].get('genres', [])
        if genres:
            for genre in genres:
                print(f"- {genre}")
        else:
            print("No genres found for this artist")
            # Ask user if they want to add genres manually
            response = input("\nDo you want to add genres manually? (y/n): ")
            if response.lower() == 'y':
                genres_input = input("Enter genres (comma-separated): ")
                manual_genres = [genre.strip() for genre in genres_input.split(',')]
                if manual_genres:
                    update_tracks_for_artist(artist_id, manual_genres, cache)
                    print(f"Added manual genres: {', '.join(manual_genres)}")
    except Exception as e:
        print(f"Error getting artist data: {str(e)}")

def search_artist_by_name(artist_name: str) -> List[Dict[str, Any]]:
    """Search for an artist by name and return results"""
    try:
        results = sp.search(q=artist_name, type='artist', limit=10)
        return results['artists']['items']
    except Exception as e:
        print(f"Error searching for artist: {str(e)}")
        return []

def check_artist_id_by_name():
    print("\n🔍 Check Artist ID by Name")
    print("=" * 60)
    artist_name = input("Enter artist name to search: ").strip()
    if not artist_name:
        print("❌ No artist name provided")
        return
    print(f"🔍 Searching for '{artist_name}'...")
    results = search_artist_by_name(artist_name)
    if not results:
        print("❌ No artists found")
        return
    print(f"\n📊 Found {len(results)} artists:")
    for i, artist in enumerate(results, 1):
        print(f"   {i}. {artist['name']} ({artist['id']})")
        if artist.get('genres'):
            print(f"      Current genres: {', '.join(artist['genres'])}")
        else:
            print(f"      No genres in Spotify")
    try:
        choice = int(input(f"\nSelect artist (1-{len(results)}), or 0 to cancel: ")) - 1
        if choice == -1:
            print("Cancelled.")
            return
        if choice < 0 or choice >= len(results):
            print("❌ Invalid selection")
            return
        selected_artist = results[choice]
        artist_id = selected_artist['id']
        artist_name = selected_artist['name']
        print(f"\n🎤 Selected: {artist_name}")
        print(f"Artist ID: {artist_id}")
        # Optionally, show genres
        if selected_artist.get('genres'):
            print(f"Genres: {', '.join(selected_artist['genres'])}")
        else:
            print("No genres found for this artist")
        # Ask if user wants to see genres and update cache
        see_genres = input("\nDo you want to see genres and update cache for this artist? (y/n): ")
        if see_genres.lower() == 'y':
            print_artist_genres(artist_id)
    except ValueError:
        print("❌ Invalid input")
        return


def main_menu():
    print("🎵 Artist Checker")
    print("=" * 60)
    while True:
        print("\nOptions:")
        print("1. Check artist ID by name")
        print("2. Check artist genres by Spotify URL")
        print("3. Check artist genres by artist code (ID)")
        print("4. Exit")
        choice = input("\nSelect option (1-4): ").strip()
        if choice == '2':
            url = input("Enter Spotify artist URL: ")
            try:
                artist_id = extract_artist_id_from_url(url)
                print(f"Extracted artist ID: {artist_id}")
                print_artist_genres(artist_id)
            except ValueError as e:
                print(f"Error: {e}")
                print("Please make sure the URL is a valid Spotify artist URL")
            except Exception as e:
                print(f"Unexpected error: {str(e)}")
        elif choice == '1':
            check_artist_id_by_name()
        elif choice == '3':
            artist_id = input("Enter Spotify artist code (ID): ").strip()
            if not artist_id:
                print("❌ No artist code provided")
            else:
                print_artist_genres(artist_id)
        elif choice == '4':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid option")

if __name__ == "__main__":
    main_menu()
