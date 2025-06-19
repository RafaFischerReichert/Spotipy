from typing import Dict, Any
import json
from Playlist_Tools import sp
from spotify_client import get_artist_with_retry
from Genre_Tools import load_artist_cache

# Cache file path
ARTIST_CACHE_FILE = "artist_genre_cache.json"

def list_artists_without_genres():
    """List all artists that have no genres and save to JSON format"""
    # Load artist cache
    artist_cache = load_artist_cache()
    
    # Find artists without genres
    artists_without_genres = [
        artist_id for artist_id, data in artist_cache.items() 
        if not data['genres']
    ]
    
    if not artists_without_genres:
        print("No artists without genres found in cache.")
        return
    
    print(f"Found {len(artists_without_genres)} artists without genres in cache.")
    
    # Process artists in batches of 50
    batch_size = 50
    artists_data = {}
    
    for i in range(0, len(artists_without_genres), batch_size):
        batch_artist_ids = artists_without_genres[i:i + batch_size]
        
        try:
            # Get artist data in batch
            artists = sp.artists(batch_artist_ids)
            
            for artist in artists['artists']:
                if artist:  # Check if artist exists
                    artist_id = artist['id']
                    artist_name = artist['name']
                    
                    # Format for JSON storage
                    artists_data[artist_id] = {
                        "name": artist_name,
                        "genres": []  # Empty genres list
                    }
                    
        except Exception as e:
            print(f"Error getting batch of artists: {str(e)}")
            # Fallback to individual requests
            for artist_id in batch_artist_ids:
                try:
                    artist = get_artist_with_retry(artist_id)
                    artist_name = artist['name']
                    
                    # Format for JSON storage
                    artists_data[artist_id] = {
                        "name": artist_name,
                        "genres": []  # Empty genres list
                    }
                    
                except Exception as e2:
                    print(f"Error getting artist info for {artist_id}: {str(e2)}")
                    continue
    
    # Save results to JSON file
    save_artists_to_json(artists_data)
    
    # Also save to text file for backward compatibility
    save_artists_to_text(artists_data)

def save_artists_to_json(artists_data: Dict[str, Dict[str, Any]]):
    """Save artists data to JSON file"""
    with open('artists_without_genres.json', 'w', encoding='utf-8') as f:
        json.dump(artists_data, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(artists_data)} artists to artists_without_genres.json")

def save_artists_to_text(artists_data: Dict[str, Dict[str, Any]]):
    """Save artists data to text file in the original format for backward compatibility"""
    # Sort artists by name for consistent output
    sorted_artists = dict(sorted(artists_data.items(), key=lambda x: x[1]['name'] if x[1] else ''))
    
    with open('artists_without_genres.txt', 'w', encoding='utf-8') as f:
        for artist_id, artist_info in sorted_artists.items():
            artist_name = artist_info['name'] if artist_info else "Unknown"
            f.write(f"    '{artist_id}': [  # {artist_name}\n")
            f.write("        \n")
            f.write("    ],\n")

if __name__ == "__main__":
    list_artists_without_genres()