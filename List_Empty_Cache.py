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
    """List all artists that have no genres and their tracks with optimized batch processing"""
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
    
    # Group artists by country
    country_artists: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    
    # Process artists in batches of 50
    batch_size = 50
    for i in range(0, len(artists_without_genres), batch_size):
        batch_artist_ids = artists_without_genres[i:i + batch_size]
        
        try:
            # Get artist data in batch
            artists = sp.artists(batch_artist_ids)
            
            for artist in artists['artists']:
                if artist:  # Check if artist exists
                    artist_id = artist['id']
                    country = artist.get('country', 'Unknown')
                    
                    artist_data = {
                        "name": artist['name'],
                        "id": artist_id,
                        "popularity": artist.get('popularity', 0),
                        "followers": artist.get('followers', {}).get('total', 0)
                    }
                    
                    country_artists[country].append(artist_data)
                    
        except Exception as e:
            print(f"Error getting batch of artists: {str(e)}")
            # Fallback to individual requests
            for artist_id in batch_artist_ids:
                try:
                    artist = get_artist_with_retry(artist_id)
                    country = artist.get('country', 'Unknown')
                    
                    artist_data = {
                        "name": artist['name'],
                        "id": artist_id,
                        "popularity": artist.get('popularity', 0),
                        "followers": artist.get('followers', {}).get('total', 0)
                    }
                    
                    country_artists[country].append(artist_data)
                    
                except Exception as e2:
                    print(f"Error getting artist info for {artist_id}: {str(e2)}")
                    continue
    
    # Build results
    results = {
        "artists": [],
        "summary": {},
        "country_distribution": {}
    }
    
    # Sort artists by popularity within each country
    for country, artists in country_artists.items():
        sorted_artists = sorted(artists, key=lambda x: (-x['popularity'], x['name']))
        results["artists"].extend(sorted_artists)
    
    # Calculate summary
    total_artists = len(results["artists"])
    total_countries = len(country_artists)
    
    results["summary"] = {
        "total_artists": total_artists,
        "total_countries": total_countries
    }
    
    # Calculate country distribution
    country_distribution = {
        country: len(artists)
        for country, artists in sorted(
            country_artists.items(),
            key=lambda x: (-len(x[1]), x[0])  # Sort by count (descending) then alphabetically
        )
    }
    
    results["country_distribution"] = country_distribution
    
    # Delete existing JSON file if it exists
    if os.path.exists('artists_without_genres.json'):
        os.remove('artists_without_genres.json')
    
    # Save results to JSON file
    with open('artists_without_genres.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Print summary to console
    print(f"\nFound {total_artists} artists without genres across {total_countries} countries")
    print("\nCountry distribution:")
    for country, count in country_distribution.items():
        print(f"- {country}: {count} artists")

if __name__ == "__main__":
    list_artists_without_genres()