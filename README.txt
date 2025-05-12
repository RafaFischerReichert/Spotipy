# Spotify Playlist and Artist Tools

## Prerequisites
- Python 3.x installed
- Spotify account
- Required Python packages: spotipy (install via `pip install spotipy`)

## Playlist Creation Tool
This tool helps you create a Spotify playlist based on your preferences.

1. Set up authentication:
   - Rename `config_template.py` to `config.py`
   - Follow the instructions in `config.py` to create your Spotify Client ID and Secret
   - These credentials can be obtained from https://developer.spotify.com/dashboard

2. Configure the playlist:
   - Open `PlaylistCreator.py`
   - Modify the last two lines to set your target playlist ID:
     ```
     playlist_id = "your_playlist_id_here"
     ```
   - You can find a playlist ID in its Spotify URL: 
     `https://open.spotify.com/playlist/THIS_IS_THE_PLAYLIST_ID`

3. Run the tool:
   - Execute `PlaylistCreator.py`
   - A browser window will open for Spotify authentication
   - If not logged in, log in to your Spotify account
   - You'll be redirected to a Postman authentication page
   - Copy the entire URL from your browser and paste it into the console
   - Wait for the script to process your playlist
   - The script will add tracks to your specified playlist

## Artist Genre Checker
This tool displays the genres associated with a Spotify artist.

1. Find the artist's ID:
   - Go to the artist's Spotify page
   - The ID is in the URL: `https://open.spotify.com/artist/THIS_IS_THE_ARTIST_ID`

2. Run the checker:
   - Open `ArtistChecker.py`
   - Replace the artist ID in the main section
   - Run the script
   - The console will display all genres associated with the artist

## Troubleshooting
- If you encounter authentication errors, ensure your Client ID and Secret are correct
- Make sure you have the necessary permissions on your Spotify account
- Verify that the playlist ID exists and you have access to it 