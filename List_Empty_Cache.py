import spotipy
from spotipy.oauth2 import SpotifyOAuth
from typing import Dict, List, Set, Any
from collections import defaultdict
import json
import os
from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI
from Playlist_Tools import sp, load_track_cache, get_artist_with_retry

def get_track_info(track_id: str) -> Dict[str, Any]:
    """Get track information from Spotify"""
    try:
        return sp.track(track_id)
    except Exception as e:
        print(f"Error getting track info for {track_id}: {str(e)}")
        return None

def list_tracks_without_genres():
    """List all tracks in the cache that have no genres and group them by artist"""
    # Load the cache
    cache = load_track_cache()
    
    # Group tracks by artist
    artist_tracks: Dict[str, Set[str]] = defaultdict(set)
    artist_names: Dict[str, str] = {}
    artist_countries: Dict[str, str] = {}
    
    # First pass: collect all tracks and their artists
    for track_id, genres in cache.items():
        if not genres:  # Only process tracks with no genres
            track_info = get_track_info(track_id)
            if not track_info:
                continue
                
            track_name = track_info['name']
            for artist in track_info['artists']:
                artist_id = artist['id']
                artist_name = artist['name']
                artist_tracks[artist_id].add(f"{track_name} ({track_id})")
                artist_names[artist_id] = artist_name
    
    # Second pass: get artist countries and build results
    results = {
        "artists": [],
        "summary": {},
        "country_distribution": {}
    }
    
    for artist_id, tracks in artist_tracks.items():
        try:
            artist = get_artist_with_retry(artist_id)
            country = artist.get('country', 'Unknown')
            artist_countries[artist_id] = country
            
            artist_data = {
                "name": artist_names[artist_id],
                "id": artist_id,
                "country": country,
                "tracks": sorted(list(tracks))
            }
            results["artists"].append(artist_data)
            
        except Exception as e:
            artist_data = {
                "name": artist_names[artist_id],
                "id": artist_id,
                "error": str(e),
                "tracks": sorted(list(tracks))
            }
            results["artists"].append(artist_data)
    
    # Calculate summary
    total_artists = len(artist_tracks)
    total_tracks = sum(len(tracks) for tracks in artist_tracks.values())
    
    results["summary"] = {
        "total_artists": total_artists,
        "total_tracks": total_tracks
    }
    
    # Calculate country distribution
    country_distribution = defaultdict(int)
    for artist_id in artist_tracks.keys():
        country = artist_countries.get(artist_id, 'Unknown')
        country_distribution[country] += 1
    
    results["country_distribution"] = {
        country: count 
        for country, count in sorted(country_distribution.items(), key=lambda x: (-x[1], x[0]))
    }
    
    # Delete existing JSON file if it exists
    if os.path.exists('tracks_without_genres.json'):
        os.remove('tracks_without_genres.json')
    
    # Save results to JSON file
    with open('tracks_without_genres.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    list_tracks_without_genres()