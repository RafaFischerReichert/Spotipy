#!/usr/bin/env python3
"""Fixes existing custom genres and redoes playlist additions.

This script:
1. Loads existing custom genres from custom_artist_genres.json
2. Normalizes all genres using the same logic as Artist_Cacher and Update_Cache
3. Updates the custom_artist_genres.json file with normalized genres
4. Updates the artist cache with the corrected custom genres
5. Redoes playlist additions with the fixed data
6. ONLY works with tracks from the original playlist (no external tracks)
"""

import time
from typing import Dict, List, Set, Any
from config import REQUESTS_PER_SECOND, PLAYLIST_ID
from spotify_client import sp
from Playlist_Tools import get_existing_playlists, get_playlist_track_ids, RateLimiter, get_playlist_tracks, find_matching_playlists
from Genre_Tools import normalize_genre, load_artist_cache, save_artist_cache, deduplicate_hyphen_genres
from Artist_Genres import load_custom_genres, save_custom_genres

def fix_custom_genres() -> Dict[str, Dict[str, Any]]:
    """Fix existing custom genres by normalizing them using the same logic as other scripts.
    
    Returns:
        Dictionary of fixed custom genres.
    """
    print("🔧 Fixing existing custom genres...")
    
    # Load existing custom genres
    custom_genres = load_custom_genres()
    if not custom_genres:
        print("❌ No custom genres found to fix")
        return {}
    
    print(f"📊 Found {len(custom_genres)} artists with custom genres")
    
    fixed_genres = {}
    total_fixed = 0
    
    for artist_id, artist_data in custom_genres.items():
        if isinstance(artist_data, dict) and 'genres' in artist_data:
            raw_genres = artist_data['genres']
            artist_name = artist_data.get('name', f'Artist_{artist_id}')
            
            # Normalize genres using the same logic as Artist_Cacher and Update_Cache
            if raw_genres:
                # Apply normalize_genre to each genre and flatten
                normalized = []
                for g in raw_genres:
                    normalized.extend(normalize_genre(g))
                
                # Remove duplicates while preserving order
                normalized_genres = list(dict.fromkeys(normalized))
                
                # Deduplicate hyphen genres before saving (same as other scripts)
                normalized_genres = deduplicate_hyphen_genres(normalized_genres)
                
                # Check if normalization changed anything
                if normalized_genres != raw_genres:
                    print(f"🎤 {artist_name}:")
                    print(f"   Raw: {raw_genres}")
                    print(f"   Fixed: {normalized_genres}")
                    total_fixed += 1
                
                fixed_genres[artist_id] = {
                    "name": artist_name,
                    "genres": normalized_genres
                }
            else:
                fixed_genres[artist_id] = {
                    "name": artist_name,
                    "genres": []
                }
        else:
            # Keep as is if not in expected format
            fixed_genres[artist_id] = artist_data
    
    print(f"✅ Fixed genres for {total_fixed} artists")
    
    # Save fixed genres back to file
    save_custom_genres(fixed_genres)
    print("💾 Saved fixed custom genres to custom_artist_genres.json")
    
    return fixed_genres

def update_artist_cache_with_fixed_genres(fixed_genres: Dict[str, Dict[str, Any]]) -> None:
    """Update the artist cache with the fixed custom genres.
    
    Args:
        fixed_genres: Dictionary of fixed custom genres to update the cache with.
    """
    print("\n🔄 Updating artist cache with fixed custom genres...")
    
    # Load existing cache
    artist_cache = load_artist_cache()
    
    # Update cache with fixed genres
    for artist_id, fixed_data in fixed_genres.items():
        custom_genre_list = fixed_data['genres']
        
        if artist_id in artist_cache:
            # Update existing entry with custom genres
            artist_cache[artist_id]['genres'] = custom_genre_list.copy()
        else:
            # Create new entry
            artist_cache[artist_id] = {
                'name': fixed_data.get('name', f'Artist_{artist_id}'),
                'genres': custom_genre_list,
                'country': None
            }
    
    # Save updated cache
    save_artist_cache(artist_cache)
    
    print("✅ Updated artist cache with fixed custom genres")

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

def redo_playlist_additions(fixed_genres: Dict[str, Dict[str, Any]]) -> None:
    """Redo playlist additions with the fixed custom genres.
    
    Args:
        fixed_genres: Dictionary of fixed custom genres to use for playlist creation.
    """
    print("\n🎵 Redoing playlist additions with fixed custom genres...")
    print(f"📋 Working with original playlist: {PLAYLIST_ID}")
    
    # Initialize rate limiter
    rate_limiter = RateLimiter(requests_per_second=REQUESTS_PER_SECOND)
    
    # Get tracks from original playlist, grouped by artist
    original_artist_tracks = get_original_playlist_tracks_by_artist()
    
    # Get existing playlists
    existing_playlists = get_existing_playlists()
    print(f"📊 Found {len(existing_playlists)} existing playlists")
    
    # Filter artists that have genres AND appear in the original playlist
    artists_with_genres = {
        artist_id: data for artist_id, data in fixed_genres.items()
        if isinstance(data, dict) and data.get('genres') and artist_id in original_artist_tracks
    }
    
    if not artists_with_genres:
        print("❌ No artists with populated genres found in original playlist")
        return
    
    print(f"📊 Processing {len(artists_with_genres)} artists with fixed genres from original playlist")
    
    # Collect all tracks by normalized genre for potential new playlist creation
    genre_tracks: Dict[str, Set[str]] = {}
    
    # Process each artist
    total_updates = 0
    artists_processed = 0
    playlists_updated = set()
    
    for artist_id, artist_data in artists_with_genres.items():
        artist_name = artist_data.get('name', f'Artist_{artist_id}')
        raw_genres = artist_data['genres']  # These are already normalized from the fix
        
        # Get tracks for this artist from the original playlist
        artist_tracks = original_artist_tracks[artist_id]
        
        print(f"\n🎤 Processing: {artist_name}")
        print(f"   Fixed genres: {', '.join(raw_genres)}")
        print(f"   Tracks in original playlist: {len(artist_tracks)}")
        
        # Normalize all genres first (for playlist matching)
        all_normalized_genres = set()
        for raw_genre in raw_genres:
            normalized_genres = normalize_genre(raw_genre)
            all_normalized_genres.update(normalized_genres)
        
        print(f"   Normalized for playlists: {', '.join(all_normalized_genres)}")
        
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
                print(f"   ❌ Error updating playlist {playlist_id}: {str(e)}")
                continue
        
        artists_processed += 1
        
        # Progress update every 10 artists
        if artists_processed % 10 == 0:
            print(f"\n📈 Progress: {artists_processed}/{len(artists_with_genres)} artists processed")
            print(f"📈 Total tracks added: {total_updates}")
    
    # Check for genres that could create new playlists (100+ tracks threshold)
    print("\n" + "=" * 60)
    print("CHECKING FOR NEW PLAYLIST OPPORTUNITIES")
    print("=" * 60)
    
    new_playlists_created = 0
    
    for norm_genre, track_ids in genre_tracks.items():
        if len(track_ids) >= 100:  # 100-track threshold
            playlist_name = f"{norm_genre.title()}"
            
            # Check if playlist already exists
            if playlist_name not in existing_playlists:
                print(f"\n🎵 Normalized genre '{norm_genre}' has {len(track_ids)} tracks - creating new playlist")
                
                # Convert set to list for playlist creation
                track_ids_list = list(track_ids)
                
                if create_new_playlist(playlist_name, track_ids_list, rate_limiter):
                    new_playlists_created += 1
                    total_updates += len(track_ids_list)
            else:
                print(f"🎵 Normalized genre '{norm_genre}' has {len(track_ids)} tracks - playlist already exists")
    
    # Final summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"🎤 Artists processed: {artists_processed}")
    print(f"📊 Total tracks added: {total_updates}")
    print(f"📋 Existing playlists updated: {len(playlists_updated)}")
    print(f"🆕 New playlists created: {new_playlists_created}")
    print("✅ Custom genre fix and playlist redo completed!")

def main():
    """Main function to fix custom genres and redo playlist additions"""
    print("🔧 Custom Genre Fixer and Playlist Redo")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # Step 1: Fix existing custom genres
        fixed_genres = fix_custom_genres()
        
        if not fixed_genres:
            print("❌ No custom genres to fix. Exiting.")
            return
        
        # Step 2: Update artist cache with fixed genres
        update_artist_cache_with_fixed_genres(fixed_genres)
        
        # Step 3: Redo playlist additions with fixed data
        redo_playlist_additions(fixed_genres)
        
        elapsed_time = time.time() - start_time
        print(f"\n⏱️  Total execution time: {elapsed_time:.2f} seconds")
        print("🎉 Fix and redo process completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during fix and redo process: {str(e)}")

if __name__ == "__main__":
    main() 