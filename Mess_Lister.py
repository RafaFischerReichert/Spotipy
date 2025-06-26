# ---
# Mess_Lister.py
# Lists and exports artists with more than a specified number of genres.
# Useful for identifying and analyzing artists with excessive or messy genre assignments in the cache.
# ---
import json
from typing import List, Dict
from Genre_Tools import load_artist_cache

def list_artists_with_multiple_genres(min_genres: int = 2) -> List[str]:
    """
    List all artist IDs that have more than the specified number of genres.
    
    Args:
        min_genres: Minimum number of genres required (default: 2)
    
    Returns:
        List of artist IDs that have more than min_genres genres
    """
    # Load artist cache
    artist_cache = load_artist_cache()
    
    # Find artists with more than min_genres genres
    artists_with_multiple_genres = []
    
    for artist_id, data in artist_cache.items():
        genres = data.get('genres', [])
        if len(genres) > min_genres:
            artists_with_multiple_genres.append(artist_id)
    
    return artists_with_multiple_genres

def export_artists_with_multiple_genres(min_genres: int = 2, output_file: str = "artists_with_multiple_genres.json"):
    """
    Export all artists that have more than the specified number of genres to a JSON file.
    
    Args:
        min_genres: Minimum number of genres required (default: 2)
        output_file: Name of the output JSON file (default: "artists_with_multiple_genres.json")
    """
    # Load artist cache
    artist_cache = load_artist_cache()
    
    # Find artists with more than min_genres genres
    artists_with_multiple_genres = list_artists_with_multiple_genres(min_genres)
    
    # Prepare data for export
    export_data = {
        "min_genres_threshold": min_genres,
        "total_artists_found": len(artists_with_multiple_genres),
        "artists": []
    }
    
    for artist_id in artists_with_multiple_genres:
        genres = artist_cache[artist_id]['genres']
        artist_data = {
            "artist_id": artist_id,
            "genres": genres,
            "genre_count": len(genres)
        }
        export_data["artists"].append(artist_data)
    
    # Export to JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    print(f"Exported {len(artists_with_multiple_genres)} artists with more than {min_genres} genres to {output_file}")

def print_artists_with_multiple_genres(min_genres: int = 2):
    """
    Print all artists that have more than the specified number of genres.
    
    Args:
        min_genres: Minimum number of genres required (default: 2)
    """
    # Load artist cache
    artist_cache = load_artist_cache()
    
    # Find artists with more than min_genres genres
    artists_with_multiple_genres = list_artists_with_multiple_genres(min_genres)
    
    print(f"\n=== Artists with more than {min_genres} genres ===")
    print(f"Found {len(artists_with_multiple_genres)} artists\n")
    
    for i, artist_id in enumerate(artists_with_multiple_genres, 1):
        genres = artist_cache[artist_id]['genres']
        
        print(f"{i}. {artist_id}")
        print(f"   Genres: {', '.join(genres)}")
        print()

if __name__ == "__main__":
    export_artists_with_multiple_genres(12)
