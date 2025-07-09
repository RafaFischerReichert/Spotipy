# Spotipy

Spotipy is a modular Python application for managing and analyzing Spotify playlists and artist genres. It provides tools for genre ranking, playlist creation, artist caching, and more, with a clear separation between controller, model, and view components.

## Features
- Backup and create Spotify playlists
- List, rank, and manage genres
- Cache and check artist information
- Manual and automated genre/country input
- Update and fix custom genres
- Modular MVC-like structure for easy extension

## Project Structure
```
Spotipy/
  app.py                  # Main entry point
  controller/             # Business logic and orchestration
  model/                  # Data models and Spotify/Wikipedia API tools
  view/                   # CLI/GUI views for user interaction
  data/                   # Data storage (cache, backups, etc.)
```

## Installation
1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/spotipy.git
   cd spotipy
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   *(Create a `requirements.txt` if not present, listing all needed packages such as `spotipy`, `requests`, etc.)*

## Usage

### Web Interface
Run the main Streamlit application:
```bash
python app.py
```

### Command Line Interface
You can run individual scripts directly from the command line using Python's module system:

#### Artist Caching & Management
```bash
# Cache all artists from the configured playlist
python -m controller.Artist_Cacher

# Update existing cache with latest genre/country data
python -m controller.Update_Cache

# Check and manage individual artists
python -m controller.Artist_Checker

# List artists without genres
python -m controller.List_Empty_Cache
```

#### Genre Management
```bash
# Add custom genres for artists
python -m controller.Add_Custom_Genres

# Manual genre input for artists without genres
python -m controller.Manual_Genre_Inputs

# Fix and normalize custom genres
python -m controller.Fix_Custom_Genres

# List and rank genres
python -m controller.Genre_Lister
python -m controller.Genre_Ranker
```

#### Playlist Operations
```bash
# Create genre-based playlists
python -m controller.Playlist_Creator

# Backup playlists
python -m controller.Playlist_Backup

# Manual country inputs for artists
python -m controller.Manual_Country_Inputs
```

#### System & Maintenance
```bash
# Run the complete genre playlist creation process
python -m controller.Main

# Check Spotify API status
python -m controller.check_api_status
```

### Configuration
- Copy `model/config_template.py` to `config.py` and fill in your Spotify API credentials and other settings as needed.
- Place `config.py` in the `model/` directory.

## Contributing
Contributions are welcome! Please open issues or submit pull requests for improvements or bug fixes.

## License
This project is licensed under the MIT License.
