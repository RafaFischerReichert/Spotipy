import time
from typing import Dict, Any
from spotify_client import sp, get_artist_with_retry
from Genre_Tools import load_artist_cache, save_artist_cache, get_custom_artist_genres
from tqdm import tqdm
from WikipediaAPI import get_artist_genres as get_wikipedia_genres

BATCH_SIZE = 50

if __name__ == "__main__":
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
                    genres = artist.get('genres', [])
                    # Fetch Wikipedia genres and combine
                    wikipedia_genres = get_wikipedia_genres(artist['name']) or []
                    all_genres = list(dict.fromkeys(genres + wikipedia_genres))
                    # Add custom genres if available
                    custom_genres = get_custom_artist_genres(artist_id)
                    all_genres.extend([g for g in custom_genres if g not in all_genres])
                    # Add national level genres
                    if artist.get('country') == 'BR':
                        all_genres.append('brazilian music')
                    elif artist.get('country') == 'JP':
                        all_genres.append('Japanese Music')
                    # Update cache
                    artist_cache[artist_id] = {
                        'genres': all_genres,
                        'country': artist.get('country')
                    }
                    updated_count += 1
            time.sleep(0.1)  # Be nice to the API
        except Exception as e:
            print(f"Error updating batch {i//BATCH_SIZE+1}: {str(e)}")
            # Fallback to individual requests
            for artist_id in batch_ids:
                try:
                    artist_data = get_artist_with_retry(artist_id)
                    genres = artist_data.get('genres', [])
                    # Fetch Wikipedia genres and combine
                    wikipedia_genres = get_wikipedia_genres(artist_data['name']) or []
                    all_genres = list(dict.fromkeys(genres + wikipedia_genres))
                    custom_genres = get_custom_artist_genres(artist_id)
                    all_genres.extend([g for g in custom_genres if g not in all_genres])
                    if artist_data.get('country') == 'BR':
                        all_genres.append('brazilian music')
                    elif artist_data.get('country') == 'JP':
                        all_genres.append('Japanese Music')
                    artist_cache[artist_id] = {
                        'genres': all_genres,
                        'country': artist_data.get('country')
                    }
                    updated_count += 1
                    time.sleep(0.1)
                except Exception as e2:
                    print(f"  Error updating artist {artist_id}: {str(e2)}")
                    continue

    save_artist_cache(artist_cache)
    elapsed = time.time() - start_time
    print(f"\n✅ Updated {updated_count} artists in {elapsed:.1f} seconds.") 