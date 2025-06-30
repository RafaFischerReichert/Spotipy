"""Updates all artists in the cache with the latest genres and country info.

This module updates all artists in the cache with the latest genres and country 
info from Spotify and Wikipedia. Uses batch processing for efficiency and 
saves the updated cache.
"""

import time
from typing import Dict, Any
from model.spotify_client import sp, get_artist_with_retry
from model.Genre_Tools import load_artist_cache, save_artist_cache, get_custom_artist_genres, normalize_genre, deduplicate_hyphen_genres
from tqdm import tqdm
from model.WikipediaAPI import get_artist_genres as get_wikipedia_genres, get_artist_country_wikidata

BATCH_SIZE = 50

def main():
    print("Updating all artists in the cache...")
    artist_cache: Dict[str, Dict[str, Any]] = load_artist_cache()
    artist_ids = list(artist_cache.keys())
    total_artists = len(artist_ids)
    updated_count = 0
    start_time = time.time()

    for i in tqdm(range(0, total_artists, BATCH_SIZE), desc="Updating artist batches"):
        batch_ids = artist_ids[i:i+BATCH_SIZE]
        try:
            artists = sp.artists(batch_ids)
            for artist in artists['artists']:
                if artist:
                    artist_id = artist['id']
                    artist_name = artist['name']
                    genres = artist.get('genres', [])
                    # Fetch Wikipedia genres and combine
                    wikipedia_genres = get_wikipedia_genres(artist_name) or []
                    all_genres = list(dict.fromkeys(genres + wikipedia_genres))
                    # Add custom genres if available
                    custom_genres = get_custom_artist_genres(artist_id)
                    all_genres.extend([g for g in custom_genres if g not in all_genres])
                    # Apply normalize_genre to each genre and flatten
                    normalized = []
                    for g in all_genres:
                        normalized.extend(normalize_genre(g))
                    # Remove duplicates while preserving order
                    all_genres = list(dict.fromkeys(normalized))
                    # Get country from cache or Wikipedia/Wikidata
                    country = artist_cache.get(artist_id, {}).get('country')
                    if not country:
                        country = get_artist_country_wikidata(artist_name)
                    # Add national level genres based on Wikipedia country
                    if country:
                        if 'Brazil' in country:
                            all_genres.append('brazilian music')
                        elif 'Japan' in country:
                            all_genres.append('Japanese Music')
                    # Deduplicate hyphen genres before saving
                    all_genres = deduplicate_hyphen_genres(all_genres)
                    artist_cache[artist_id] = {
                        'name': artist_name,
                        'genres': all_genres,
                        'country': country
                    }
                    updated_count += 1
            time.sleep(0.1)
        except Exception as e:
            print(f"Error updating batch {i//BATCH_SIZE+1}: {str(e)}")
            # Fallback to individual requests
            for artist_id in batch_ids:
                try:
                    artist_data = get_artist_with_retry(artist_id)
                    artist_name = artist_data['name']
                    genres = artist_data.get('genres', [])
                    # Fetch Wikipedia genres and combine
                    wikipedia_genres = get_wikipedia_genres(artist_name) or []
                    all_genres = list(dict.fromkeys(genres + wikipedia_genres))
                    custom_genres = get_custom_artist_genres(artist_id)
                    all_genres.extend([g for g in custom_genres if g not in all_genres])
                    # Apply normalize_genre to each genre and flatten
                    normalized = []
                    for g in all_genres:
                        normalized.extend(normalize_genre(g))
                    all_genres = list(dict.fromkeys(normalized))
                    # Get country from cache or Wikipedia/Wikidata
                    country = artist_cache.get(artist_id, {}).get('country')
                    if not country:
                        country = get_artist_country_wikidata(artist_name)
                    if country:
                        if 'Brazil' in country:
                            all_genres.append('brazilian music')
                        elif 'Japan' in country:
                            all_genres.append('Japanese Music')
                    # Deduplicate hyphen genres before saving
                    all_genres = deduplicate_hyphen_genres(all_genres)
                    artist_cache[artist_id] = {
                        'name': artist_name,
                        'genres': all_genres,
                        'country': country
                    }
                    updated_count += 1
                    time.sleep(0.1)
                except Exception as e2:
                    print(f"  Error updating artist {artist_id}: {str(e2)}")
                    continue

    save_artist_cache(artist_cache)
    elapsed = time.time() - start_time
    print(f"\nUpdated {updated_count} artists in {elapsed:.1f} seconds") 