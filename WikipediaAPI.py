# ---
# WikipediaAPI.py
# Provides functions to fetch genres and country information for artists from Wikipedia and Wikidata.
# Used to supplement Spotify data with additional genre and country info for improved accuracy.
# ---
import requests
import mwparserfromhell
import re

def get_artist_genres(artist_name):
    # Step 1: Format artist name for Wikipedia
    page_title = artist_name.replace(" ", "_")

    # Step 2: Call Wikipedia API to get wikitext
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "prop": "revisions",
        "titles": page_title,
        "rvslots": "main",
        "rvprop": "content"
    }

    response = requests.get(url, params=params)
    data = response.json()

    # Step 3: Extract wikitext from response
    pages = data["query"]["pages"]
    page = next(iter(pages.values()))
    if "revisions" not in page:
        return None  # Page not found or no revisions

    wikitext = page["revisions"][0]["slots"]["main"]["*"]

    # Step 4: Parse the wikitext using mwparserfromhell
    wikicode = mwparserfromhell.parse(wikitext)
    templates = wikicode.filter_templates()

    for template in templates:
        if template.name.strip().lower().startswith("infobox"):
            if template.has("genre"):
                genres_raw = template.get("genre").value
                genres = parse_complex_genres(genres_raw)
                return [genre.lower() for genre in genres]

    return None

def parse_complex_genres(genres_raw):
    """Parse complex genre wikitext and extract clean genre names"""
    if not genres_raw:
        return []
    
    # Parse with mwparserfromhell to handle templates and links
    wikicode = mwparserfromhell.parse(str(genres_raw))
    
    # Extract text content, handling templates and links
    genres = []
    
    # Handle different patterns:
    # 1. Direct text content
    # 2. Links like [[Pop rock]] or [[new wave music|new wave]]
    # 3. Templates like {{hlist|...}}
    
    # First, try to extract from hlist templates
    hlist_templates = [t for t in wikicode.filter_templates() if t.name.strip().lower() == 'hlist']
    if hlist_templates:
        for template in hlist_templates:
            for param in template.params:
                param_text = str(param.value).strip()
                # Remove <ref>...</ref> tags before extracting links
                param_text = re.sub(r'<ref[^>]*>.*?</ref>', '', param_text, flags=re.DOTALL)
                if param_text:
                    # Extract from links like [[genre]] or [[link|display]]
                    link_matches = re.findall(r'\[\[([^|\]]+)(?:\|([^\]]+))?\]\]', param_text)
                    for match in link_matches:
                        if match[1]:  # Has display text
                            genres.append(match[1].strip())
                        else:  # No display text, use link text
                            genres.append(match[0].strip())
    
    # If no hlist found, try direct parsing
    if not genres:
        # Extract all links
        links = wikicode.filter_wikilinks()
        for link in links:
            link_text = str(link.title).strip()
            if '|' in link_text:
                # Format: [[link|display]]
                parts = link_text.split('|')
                if len(parts) >= 2:
                    genres.append(parts[1].strip())
            else:
                # Format: [[genre]]
                genres.append(link_text.strip())
    
    # If still no genres, try simple text extraction
    if not genres:
        # Remove all wiki markup and split by common separators
        text_content = wikicode.strip_code()
        # Split by common separators: comma, semicolon, newline, pipe
        parts = re.split(r'[,;\n|]', text_content)
        for part in parts:
            part = part.strip()
            if part and len(part) > 1:  # Avoid single characters
                genres.append(part)
    
    # Clean up genres: remove duplicates, empty strings, and common noise
    cleaned_genres = []
    seen = set()
    for genre in genres:
        genre = genre.strip()
        # Skip if empty, too short, or already seen
        if genre and len(genre) > 1 and genre.lower() not in seen:
            # Remove common noise words
            if genre.lower() not in ['and', 'or', 'the', 'a', 'an', 'of', 'in', 'on', 'at', 'to', 'for', 'with', 'by']:
                cleaned_genres.append(genre)
                seen.add(genre.lower())
    
    return cleaned_genres

def get_artist_country_wikidata(artist_name):
    """
    Retrieve the country of origin for an artist using Wikidata via Wikipedia API.
    Tries to find country of origin (P495), citizenship (P27), or country for musical group (P1532).
    Returns the country name as a string, or None if not found.
    """
    try:
        # Step 1: Search for the artist's Wikipedia page
        search_url = "https://en.wikipedia.org/w/api.php"
        search_params = {
            "action": "query",
            "list": "search",
            "srsearch": artist_name,
            "format": "json"
        }
        search_response = requests.get(search_url, params=search_params)
        search_data = search_response.json()
        if not search_data['query']['search']:
            return None
        page_title = search_data['query']['search'][0]['title']

        # Step 2: Get the Wikidata entity ID from the Wikipedia page
        page_url = "https://en.wikipedia.org/w/api.php"
        page_params = {
            "action": "query",
            "format": "json",
            "prop": "pageprops",
            "titles": page_title
        }
        page_response = requests.get(page_url, params=page_params)
        page_data = page_response.json()
        pages = page_data["query"]["pages"]
        page = next(iter(pages.values()))
        if "pageprops" not in page or "wikibase_item" not in page["pageprops"]:
            return None
        entity_id = page["pageprops"]["wikibase_item"]

        # Step 3: Query Wikidata for country of origin (P495), citizenship (P27), or country for musical group (P1532)
        sparql_url = "https://query.wikidata.org/sparql"
        query = f"""
        SELECT ?countryLabel WHERE {{
          OPTIONAL {{ wd:{entity_id} wdt:P495 ?country. }}
          OPTIONAL {{ wd:{entity_id} wdt:P27 ?country. }}
          OPTIONAL {{ wd:{entity_id} wdt:P1532 ?country. }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language 'en'. }}
        }}
        LIMIT 1
        """
        headers = {"Accept": "application/sparql-results+json"}
        r = requests.get(sparql_url, params={'query': query}, headers=headers)
        results = r.json()
        bindings = results['results']['bindings']
        if bindings:
            return bindings[0]['countryLabel']['value']
        else:
            return None
    except Exception as e:
        print(f"Error fetching country from Wikidata for {artist_name}: {e}")
        return None

# 🎵 Example usage
if __name__ == '__main__':
    artist = "Cutting Crew"
    genres = get_artist_genres(artist)
    print(f"Genres for {artist}:")
    print(genres if genres else "Not found")
