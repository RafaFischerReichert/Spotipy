import spotipy
from spotipy.oauth2 import SpotifyOAuth
from typing import Dict, List, Set, Any
from collections import defaultdict
import json
import os
from Playlist_Tools import sp, get_artist_with_retry, get_artists_batch
from Genre_Tools import load_artist_cache

# Cache file path
ARTIST_CACHE_FILE = "artist_genre_cache.json"

def list_artists_without_genres():
    """List all artists that have no genres in the same format as Artist_Genres"""
    # Load artist cache
    artist_cache = load_artist_cache()
    
    # Find artists without genres
    artists_without_genres = [
        artist_id for artist_id, genres in artist_cache.items() 
        if not genres
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
                    
                    # Format in the same way as Artist_Genres
                    artists_data[artist_id] = [artist_name]  # artist_name
                    
        except Exception as e:
            print(f"Error getting batch of artists: {str(e)}")
            # Fallback to individual requests
            for artist_id in batch_artist_ids:
                try:
                    artist = get_artist_with_retry(artist_id)
                    artist_name = artist['name']
                    
                    # Format in the same way as Artist_Genres
                    artists_data[artist_id] = [artist_name]  # artist_name
                    
                except Exception as e2:
                    print(f"Error getting artist info for {artist_id}: {str(e2)}")
                    continue
    
    # Sort artists by name for consistent output
    sorted_artists = dict(sorted(artists_data.items(), key=lambda x: x[1][0] if x[1] else ''))
    
    # Save results to text file in Artist_Genres format
    with open('artists_without_genres.txt', 'w', encoding='utf-8') as f:
        for artist_id, artist_info in sorted_artists.items():
            artist_name = artist_info[0] if artist_info else "Unknown"
            f.write(f"    '{artist_id}': [  # {artist_name}\n")
            f.write("        \n")
            f.write("    ],\n")

if __name__ == "__main__":
    list_artists_without_genres()