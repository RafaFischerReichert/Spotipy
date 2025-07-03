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
Run the main application or any controller script directly:
```bash
python app.py
```
Or, for specific tasks (e.g., creating a playlist):
```bash
python controller/Playlist_Creator.py
```

## Configuration
- Copy `model/config_template.py` to `config.py` and fill in your Spotify API credentials and other settings as needed.
- Place `config.py` in the `model/` directory.

## Contributing
Contributions are welcome! Please open issues or submit pull requests for improvements or bug fixes.

## License
This project is licensed under the MIT License.
