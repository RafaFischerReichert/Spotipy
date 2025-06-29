#!/usr/bin/env python3
"""Updates playlists with artists that have custom genres.

This script:
1. Loads custom genres from custom_artist_genres.json
2. Finds existing genre playlists
3. Adds artists with custom genres to their corresponding playlists
4. Creates new playlists when there are enough tracks (100+ threshold)
5. Handles duplicate prevention and batch processing
6. ONLY works with tracks from the original playlist (no external tracks)
"""

from typing import Dict, List, Set
from config import REQUESTS_PER_SECOND, PLAYLIST_ID
from spotify_client import sp
from Playlist_Tools import get_existing_playlists, get_playlist_track_ids, RateLimiter, get_playlist_tracks, find_matching_playlists
from Genre_Tools import normalize_genre
from Artist_Genres import load_custom_genres

def get_original_playlist_tracks_by_artist() -> Dict[str, List[str]]:
    """Get all tracks from the original playlist, grouped by artist ID.
    
    Returns:
        Dictionary mapping artist IDs to lists of track IDs.
    """
    print("📋 Loading tracks from original playlist...")
    
    # Get all tracks from the original playlist
    tracks = get_playlist_tracks(PLAYLIST_ID)
    
    # Group tracks by artist
    artist_tracks: Dict[str, List[str]] = {}
    
    for track in tracks:
        if track['track']:
            track_id = track['track']['id']
            for artist in track['track']['artists']:
                artist_id = artist['id']
                if artist_id not in artist_tracks:
                    artist_tracks[artist_id] = []
                artist_tracks[artist_id].append(track_id)
    
    print(f"📊 Found {len(artist_tracks)} artists in original playlist")
    print(f"📋 Working with original playlist: {PLAYLIST_ID}")
    print(f"   Tracks in original playlist: {len(artist_tracks)}")
    return artist_tracks

def create_new_playlist(playlist_name: str, track_ids: List[str], rate_limiter: RateLimiter) -> bool:
    """Create a new playlist and add tracks to it.
    
    Args:
        playlist_name: Name for the new playlist.
        track_ids: List of track IDs to add to the playlist.
        rate_limiter: Rate limiter instance for API calls.
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        user_id = sp.current_user()['id']
        
        # Create the playlist
        playlist = sp.user_playlist_create(
            user=user_id,
            name=playlist_name,
            public=True
        )
        playlist_id = playlist['id']
        
        print(f"   🆕 Created new playlist '{playlist_name}'")
        
        # Add tracks to playlist in chunks of 50
        for i in range(0, len(track_ids), 50):
            chunk = track_ids[i:i + 50]
            sp.playlist_add_items(playlist_id, chunk)
            rate_limiter.wait()
        
        print(f"   ➕ Added {len(track_ids)} tracks to '{playlist_name}'")
        return True
        
    except Exception as e:
        print(f"   ❌ Error creating playlist '{playlist_name}': {str(e)}")
        return False

def update_playlists_with_custom_genres() -> None:
    """Main function to update playlists with custom genres."""
    print("🎵 Custom Genre Playlist Updater")
    print("=" * 60)
    print(f"📋 Working with original playlist: {PLAYLIST_ID}")
    print("=" * 60)
    
    # Initialize rate limiter
    rate_limiter = RateLimiter(requests_per_second=REQUESTS_PER_SECOND)
    
    # Load custom genres
    custom_genres = load_custom_genres()
    if not custom_genres:
        print("❌ No custom genres found in custom_artist_genres.json")
        return
    
    print(f"📊 Found {len(custom_genres)} artists with custom genres")
    
    # Get tracks from original playlist, grouped by artist
    original_artist_tracks = get_original_playlist_tracks_by_artist()
    
    # Get existing playlists
    existing_playlists = get_existing_playlists()
    print(f"📊 Found {len(existing_playlists)} existing playlists")
    
    # Filter artists that have genres AND appear in the original playlist
    artists_with_genres = {
        artist_id: data for artist_id, data in custom_genres.items()
        if isinstance(data, dict) and data.get('genres') and artist_id in original_artist_tracks
    }
    
    if not artists_with_genres:
        print("❌ No artists with populated genres found in original playlist")
        return
    
    print(f"📊 Processing {len(artists_with_genres)} artists with genres from original playlist")
    
    # Collect all tracks by normalized genre for potential new playlist creation
    genre_tracks: Dict[str, Set[str]] = {}
    
    # Process each artist
    total_updates = 0
    artists_processed = 0
    playlists_updated = set()
    
    for artist_id, artist_data in artists_with_genres.items():
        artist_name = artist_data.get('name', f'Artist_{artist_id}')
        raw_genres = artist_data['genres']
        
        # Get tracks for this artist from the original playlist
        artist_tracks = original_artist_tracks[artist_id]
        
        print(f"\n🎤 Processing: {artist_name}")
        print(f"   Raw genres: {', '.join(raw_genres)}")
        print(f"   Tracks in original playlist: {len(artist_tracks)}")
        
        # Normalize all genres first
        all_normalized_genres = set()
        for raw_genre in raw_genres:
            normalized_genres = normalize_genre(raw_genre)
            all_normalized_genres.update(normalized_genres)
        
        print(f"   Normalized genres: {', '.join(all_normalized_genres)}")
        
        # Find matching playlists for each normalized genre
        playlists_to_update = set()
        for norm_genre in all_normalized_genres:
            matching_playlists = find_matching_playlists(norm_genre, existing_playlists)
            playlists_to_update.update(matching_playlists)
            
            # Also collect tracks by normalized genre for potential new playlists
            if norm_genre not in genre_tracks:
                genre_tracks[norm_genre] = set()
            genre_tracks[norm_genre].update(artist_tracks)
        
        if not playlists_to_update:
            print(f"   ⚠️  No matching playlists found for normalized genres: {', '.join(all_normalized_genres)}")
            continue
        
        print(f"   📋 Found {len(playlists_to_update)} matching playlists")
        
        # Update each matching playlist
        for playlist_id in playlists_to_update:
            try:
                # Get playlist name for display
                playlist_name = next(
                    (name for name, pid in existing_playlists.items() if pid == playlist_id),
                    f"Playlist_{playlist_id}"
                )
                
                # Get existing tracks in playlist
                existing_tracks = get_playlist_track_ids(playlist_id)
                
                # Filter out tracks that already exist
                new_tracks = [track_id for track_id in artist_tracks if track_id not in existing_tracks]
                
                if new_tracks:
                    print(f"   ➕ Adding {len(new_tracks)} tracks to '{playlist_name}'")
                    
                    # Add tracks in batches of 50
                    for i in range(0, len(new_tracks), 50):
                        batch = new_tracks[i:i + 50]
                        sp.playlist_add_items(playlist_id, batch)
                        rate_limiter.wait()
                    
                    total_updates += len(new_tracks)
                    playlists_updated.add(playlist_id)
                else:
                    print(f"   ✅ All tracks already in '{playlist_name}'")
                
            except Exception as e:
                print(f"   ❌ Error updating playlist '{playlist_name}': {str(e)}")
                continue
        
        artists_processed += 1
    
    print(f"\n✅ Custom genre update completed!")
    print(f"📊 Summary:")
    print(f"   🎤 Artists processed: {artists_processed}")
    print(f"   📋 Playlists updated: {len(playlists_updated)}")
    print(f"   ➕ Total tracks added: {total_updates}")
    
    # Check for potential new playlists
    new_playlist_candidates = {
        genre: tracks for genre, tracks in genre_tracks.items()
        if len(tracks) >= 100 and not find_matching_playlists(genre, existing_playlists)
    }
    
    if new_playlist_candidates:
        print(f"\n🎵 Potential new playlists (100+ tracks):")
        for genre, tracks in new_playlist_candidates.items():
            print(f"   - {genre}: {len(tracks)} tracks")
        
        response = input("\nCreate new playlists for these genres? (y/N): ").strip().lower()
        if response == 'y':
            for genre, track_ids in new_playlist_candidates.items():
                playlist_name = genre.title()
                create_new_playlist(playlist_name, list(track_ids), rate_limiter)

def print_custom_genres_summary():
    """Print a summary of custom genres"""
    custom_genres = load_custom_genres()
    
    if not custom_genres:
        print("❌ No custom genres found")
        return
    
    print("📊 Custom Genres Summary:")
    print("=" * 60)
    
    artists_with_genres = 0
    total_genres = 0
    
    for artist_id, artist_data in custom_genres.items():
        if isinstance(artist_data, dict) and artist_data.get('genres'):
            artists_with_genres += 1
            total_genres += len(artist_data['genres'])
    
    print(f"🎤 Artists with custom genres: {artists_with_genres}")
    print(f"🎵 Total custom genre assignments: {total_genres}")
    print(f"📊 Average genres per artist: {total_genres/artists_with_genres:.1f}")

if __name__ == "__main__":
    update_playlists_with_custom_genres() 