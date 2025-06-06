import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import json
import os
from typing import Dict, List, Set, Optional, Any, Union
from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI
from spotify_client import sp, get_artist_with_retry
from Genre_Tools import get_track_genres, load_track_cache, save_track_cache, normalize_genre

# Cache file path
CACHE_FILE = "track_genre_cache.json"

def get_playlist_tracks(playlist_id: str) -> List[Dict[str, Any]]:
    """Get all tracks from a playlist, handling pagination"""
    tracks: List[Dict[str, Any]] = []
    max_retries: int = 5
    base_delay: int = 1
    
    for attempt in range(max_retries):
        try:
            results: Dict[str, Any] = sp.playlist_tracks(playlist_id)
            tracks.extend(results['items'])
            
            while results['next']:
                results = sp.next(results)
                tracks.extend(results['items'])
                time.sleep(0.1)  # Rate limiting
            
            return tracks
        except Exception as e:
            if ('rate' in str(e).lower() or 'timeout' in str(e).lower()) and attempt < max_retries - 1:
                delay: int = base_delay * (2 ** attempt)
                print(f"Request failed ({str(e)}), waiting {delay} seconds...")
                time.sleep(delay)
            else:
                raise

def get_existing_playlists() -> Dict[str, str]:
    """Get all user playlists and return a mapping of name to id"""
    user_id: str = sp.current_user()['id']
    existing_playlists: Dict[str, str] = {}
    offset: int = 0
    
    while True:
        playlists: Dict[str, Any] = sp.current_user_playlists(limit=50, offset=offset)
        for playlist in playlists['items']:
            existing_playlists[playlist['name']] = playlist['id']
        if not playlists['next']:
            break
        offset += 50
        time.sleep(0.2)
    
    return existing_playlists

def get_playlist_track_ids(playlist_id: str) -> Set[str]:
    """Get all track IDs from a playlist"""
    existing_tracks: Set[str] = set()
    offset: int = 0
    
    while True:
        results: Dict[str, Any] = sp.playlist_items(playlist_id, limit=50, offset=offset)
        for item in results['items']:
            if item['track']:
                existing_tracks.add(item['track']['id'])
        if not results['next']:
            break
        offset += 50
        time.sleep(0.3)
    
    return existing_tracks
