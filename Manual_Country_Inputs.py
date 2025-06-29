"""Prompts the user to manually input missing country information for artists.

This module prompts the user to manually input missing country information for 
artists in the cache. Updates the cache with user-provided country data for 
each artist.
"""

from Genre_Tools import load_artist_cache, save_artist_cache, get_artist_name_from_cache

def prompt_and_update_countries():
    """Prompt the user to manually input country information for artists without countries."""
    cache = load_artist_cache()
    updated = False
    null_country_artists = [aid for aid, data in cache.items() if data.get('country') is None]
    if not null_country_artists:
        print("✅ All artists have a country set in the cache.")
        return

    print(f"Found {len(null_country_artists)} artists with no country in the cache.\n")
    for artist_id in null_country_artists:
        artist_name = get_artist_name_from_cache(artist_id, cache)
        genres = cache[artist_id].get('genres', [])
        print(f"Artist: {artist_name} (ID: {artist_id}, genres: {', '.join(genres)})")
        country = input("Enter country for this artist (or leave blank to skip): ").strip()
        if country.lower() == "exit":
            break
        elif country:
            cache[artist_id]['country'] = country
            updated = True
            save_artist_cache(cache)
            print(f"✅ Updated {artist_name} with country: {country}\n")
        else:
            print("⏭️  Skipped.\n")

    if updated:
        print("🎉 Cache updated with new country information.")
    else:
        print("No updates made to the cache.")

if __name__ == "__main__":
    prompt_and_update_countries()
