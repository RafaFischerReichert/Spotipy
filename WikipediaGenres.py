# ---
# WikipediaGenres.py
# Uses Wikipedia to fetch and normalize genres for artists missing genre data.
# Saves the results to a JSON file for further use in the genre cache or custom genres.
# ---
import json
import re
import time
from WikipediaAPI import get_artist_genres
from Genre_Tools import normalize_genre

def extract_artist_names_from_json(filename):
    """Extract artist names from the artists_without_genres.json file"""
    artists = {}
    
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        for artist_id, artist_info in data.items():
            if isinstance(artist_info, dict) and 'name' in artist_info:
                artists[artist_id] = artist_info['name']
            else:
                # Fallback for old format
                artists[artist_id] = str(artist_info)
        
        return artists
    except FileNotFoundError:
        print(f"File {filename} not found. Trying to read from text file...")
        return extract_artist_names_from_file('artists_without_genres.txt')
    except json.JSONDecodeError:
        print(f"Error reading JSON file {filename}. Trying to read from text file...")
        return extract_artist_names_from_file('artists_without_genres.txt')

def extract_artist_names_from_file(filename):
    """Extract artist names from the artists_without_genres.txt file (fallback)"""
    artists = {}
    
    with open(filename, 'r', encoding='utf-8') as file:
        content = file.read()
        
    # Use regex to find artist ID and name pairs
    pattern = r"'([^']+)':\s*\[\s*#\s*(.+?)\s*\n"
    matches = re.findall(pattern, content)
    
    for artist_id, artist_name in matches:
        artists[artist_id] = artist_name.strip()
    
    return artists

def get_genres_for_artists(artists, delay=1):
    """Get genres for each artist using Wikipedia API with rate limiting"""
    results = {}
    total_artists = len(artists)
    
    print(f"Processing {total_artists} artists...")
    
    for i, (artist_id, artist_name) in enumerate(artists.items(), 1):
        print(f"Processing {i}/{total_artists}: {artist_name}")
        
        try:
            genres = get_artist_genres(artist_name)
            
            # Normalize genres using the core normalize_genre function
            if genres:
                normalized_genres = []
                for genre in genres:
                    normalized = normalize_genre(genre)
                    if normalized:  # Only add if normalization returned results
                        normalized_genres.extend(normalized)
                
                # Remove duplicates while preserving order
                normalized_genres = list(dict.fromkeys(normalized_genres))
                print(f"   Raw genres: {genres}")
                print(f"   Normalized genres: {normalized_genres}")
            else:
                normalized_genres = []
            
            results[artist_id] = {
                "name": artist_name,
                "genres": normalized_genres
            }
            
            # Add a small delay to be respectful to Wikipedia's API
            time.sleep(delay)
            
        except Exception as e:
            print(f"Error processing {artist_name}: {str(e)}")
            results[artist_id] = {
                "name": artist_name,
                "genres": [],
                "error": str(e)
            }
    
    return results

def save_results_to_json(results, filename):
    """Save the results to a JSON file"""
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(results, file, indent=2, ensure_ascii=False)
    
    print(f"Results saved to {filename}")

def main():
    # Extract artist names from the JSON file
    print("Extracting artist names from artists_without_genres.json...")
    artists = extract_artist_names_from_json('artists_without_genres.json')
    
    print(f"Found {len(artists)} artists")
    
    # Get genres for each artist
    results = get_genres_for_artists(artists)
    
    # Save results to custom genres JSON file
    save_results_to_json(results, 'custom_artist_genres.json')
    
    # Print summary
    artists_with_genres = sum(1 for data in results.values() if data.get('genres'))
    print(f"\nSummary:")
    print(f"Total artists processed: {len(results)}")
    print(f"Artists with genres found: {artists_with_genres}")
    print(f"Artists without genres: {len(results) - artists_with_genres}")

if __name__ == '__main__':
    main()
