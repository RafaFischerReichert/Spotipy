import json
import os
import re
from typing import List, Dict, Any

# Custom genres file path
CUSTOM_GENRES_FILE = "custom_artist_genres.json"

def load_custom_genres() -> Dict[str, Dict[str, Any]]:
    """Load custom artist genres from JSON file"""
    if os.path.exists(CUSTOM_GENRES_FILE):
        try:
            with open(CUSTOM_GENRES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Custom genres file corrupted, starting with empty cache")
            return {}
    return {}

def get_custom_artist_genres(artist_id: str) -> List[str]:
    """Get custom genres for a specific artist from the JSON file"""
    custom_genres = load_custom_genres()
    
    if artist_id in custom_genres:
        artist_data = custom_genres[artist_id]
        if isinstance(artist_data, dict) and 'genres' in artist_data:
            return artist_data['genres']
        elif isinstance(artist_data, list):
            return artist_data
    
    return []

def save_custom_genres(custom_genres: Dict[str, Dict[str, Any]]) -> None:
    """Save custom artist genres to JSON file"""
    with open(CUSTOM_GENRES_FILE, 'w', encoding='utf-8') as f:
        json.dump(custom_genres, f, indent=2, ensure_ascii=False)

def add_custom_genres(artist_id: str, genres: List[str], artist_name: str = None) -> None:
    """Add or update custom genres for an artist"""
    custom_genres = load_custom_genres()
    
    custom_genres[artist_id] = {
        "name": artist_name or f"Artist_{artist_id}",
        "genres": genres
    }
    
    save_custom_genres(custom_genres)

def search_artist_by_name(artist_name: str) -> List[Dict[str, Any]]:
    """Search for an artist by name and return results"""
    from spotify_client import sp
    try:
        results = sp.search(q=artist_name, type='artist', limit=10)
        return results['artists']['items']
    except Exception as e:
        print(f"Error searching for artist: {str(e)}")
        return []

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
