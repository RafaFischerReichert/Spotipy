#!/usr/bin/env python3
"""Cleans up genre playlists by removing tracks that do not match the playlist's genre.

This module cleans up genre playlists by removing tracks that do not match the 
playlist's genre. Uses improved matching logic and batch operations to ensure 
only correct tracks remain in each genre playlist.
"""

from typing import Dict, List
from config import REQUESTS_PER_SECOND
from spotify_client import sp
from Playlist_Tools import get_existing_playlists, get_playlist_track_ids, RateLimiter, find_matching_playlists, get_playlist_genre, identify_genre_playlists
from Genre_Tools import normalize_genre, load_artist_cache, should_track_be_in_playlist

def cleanup_playlist(playlist_id: str, playlist_name: str, rate_limiter: RateLimiter) -> Dict[str, int]:
    """Clean up a single playlist by removing incorrect tracks.
    
    Args:
        playlist_id: The Spotify playlist ID to clean up.
        playlist_name: The name of the playlist for display purposes.
        rate_limiter: Rate limiter instance for API calls.
        
    Returns:
        Dictionary with statistics about the cleanup operation.
    """
    print(f"\n🧹 Cleaning playlist: {playlist_name}")
    
    # Load artist cache for faster genre lookup
    artist_cache = load_artist_cache()
    
    # Get all tracks in the playlist
    all_track_ids = get_playlist_track_ids(playlist_id)
    print(f"   📊 Found {len(all_track_ids)} tracks in playlist")
    
    # Get playlist genre
    playlist_genre = get_playlist_genre(playlist_name)
    print(f"   🎵 Playlist genre: {playlist_genre}")
    
    # Get track details to check genres
    tracks_to_remove = []
    tracks_to_keep = []
    
    # Process tracks in batches
    batch_size = 50
    for i in range(0, len(all_track_ids), batch_size):
        batch_ids = list(all_track_ids)[i:i + batch_size]
        
        try:
            # Get track details
            tracks_data = sp.tracks(batch_ids)
            
            for track_data in tracks_data['tracks']:
                if not track_data:
                    continue
                
                track_id = track_data['id']
                
                # Get genres for this track
                track_genres = []
                for artist in track_data['artists']:
                    artist_id = artist['id']
                    if artist_id in artist_cache:
                        track_genres.extend(artist_cache[artist_id]['genres'])
                
                # Check if track should be in this playlist
                if should_track_be_in_playlist(track_genres, playlist_genre):
                    tracks_to_keep.append(track_id)
                else:
                    tracks_to_remove.append(track_id)
                    print(f"   ❌ Track '{track_data['name']}' by {track_data['artists'][0]['name']} doesn't belong (genres: {track_genres})")
            
            rate_limiter.wait()
            
        except Exception as e:
            print(f"   ⚠️  Error processing batch: {str(e)}")
            continue
    
    # Remove incorrect tracks
    removed_count = 0
    if tracks_to_remove:
        print(f"   🗑️  Removing {len(tracks_to_remove)} incorrect tracks...")
        
        # Remove tracks in batches
        for i in range(0, len(tracks_to_remove), 50):
            batch = tracks_to_remove[i:i + 50]
            try:
                sp.playlist_remove_all_occurrences_of_items(playlist_id, batch)
                removed_count += len(batch)
                rate_limiter.wait()
            except Exception as e:
                print(f"   ⚠️  Error removing batch: {str(e)}")
    
    print(f"   ✅ Kept {len(tracks_to_keep)} tracks, removed {removed_count} tracks")
    
    return {
        'kept': len(tracks_to_keep),
        'removed': removed_count,
        'total': len(all_track_ids)
    }

def cleanup_all_genre_playlists() -> None:
    """Clean up all genre playlists."""
    print("🧹 Genre Playlist Cleanup Tool")
    print("=" * 60)
    
    # Initialize rate limiter
    rate_limiter = RateLimiter(requests_per_second=REQUESTS_PER_SECOND)
    
    # Get existing playlists
    existing_playlists = get_existing_playlists()
    print(f"📊 Found {len(existing_playlists)} total playlists")
    
    # Identify genre playlists
    genre_playlists = identify_genre_playlists(existing_playlists)
    print(f"🎵 Found {len(genre_playlists)} genre playlists")
    
    if not genre_playlists:
        print("❌ No genre playlists found to clean up")
        return
    
    # Show genre playlists
    print("\n🎵 Genre playlists found:")
    for i, (name, playlist_id) in enumerate(genre_playlists.items(), 1):
        print(f"   {i}. {name}")
    
    # Ask for confirmation
    print(f"\n⚠️  This will clean up {len(genre_playlists)} genre playlists.")
    print("   Tracks that don't belong to the exact genre will be removed.")
    
    response = input("\nContinue with cleanup? (y/N): ").strip().lower()
    if response != 'y':
        print("❌ Cleanup cancelled")
        return
    
    # Clean up each playlist
    total_kept = 0
    total_removed = 0
    total_tracks = 0
    
    for playlist_name, playlist_id in genre_playlists.items():
        try:
            stats = cleanup_playlist(playlist_id, playlist_name, rate_limiter)
            total_kept += stats['kept']
            total_removed += stats['removed']
            total_tracks += stats['total']
        except Exception as e:
            print(f"❌ Error cleaning playlist {playlist_name}: {str(e)}")
            continue
    
    # Final summary
    print("\n" + "=" * 60)
    print("CLEANUP SUMMARY")
    print("=" * 60)
    print(f"🎵 Playlists cleaned: {len(genre_playlists)}")
    print(f"📊 Total tracks processed: {total_tracks}")
    print(f"✅ Tracks kept: {total_kept}")
    print(f"🗑️  Tracks removed: {total_removed}")
    print("🎉 Cleanup completed!")

def preview_cleanup() -> None:
    """Preview what would be cleaned up without actually doing it."""
    print("👀 Genre Playlist Cleanup Preview")
    print("=" * 60)
    
    # Initialize rate limiter
    rate_limiter = RateLimiter(requests_per_second=REQUESTS_PER_SECOND)
    
    # Get existing playlists
    existing_playlists = get_existing_playlists()
    
    # Identify genre playlists
    genre_playlists = identify_genre_playlists(existing_playlists)
    
    if not genre_playlists:
        print("❌ No genre playlists found")
        return
    
    print(f"🎵 Found {len(genre_playlists)} genre playlists")
    
    # Load artist cache
    artist_cache = load_artist_cache()
    
    total_incorrect_tracks = 0
    
    for playlist_name, playlist_id in genre_playlists.items():
        print(f"\n🎵 Previewing: {playlist_name}")
        
        # Get playlist genre
        playlist_genre = get_playlist_genre(playlist_name)
        
        # Get all tracks in the playlist
        all_track_ids = get_playlist_track_ids(playlist_id)
        
        incorrect_tracks = []
        
        # Sample first 20 tracks for preview
        sample_tracks = list(all_track_ids)[:20]
        
        for track_id in sample_tracks:
            try:
                track_data = sp.track(track_id)
                
                # Get genres for this track
                track_genres = []
                for artist in track_data['artists']:
                    artist_id = artist['id']
                    if artist_id in artist_cache:
                        track_genres.extend(artist_cache[artist_id]['genres'])
                
                # Check if track should be in this playlist
                if not should_track_be_in_playlist(track_genres, playlist_genre):
                    incorrect_tracks.append(f"{track_data['name']} by {track_data['artists'][0]['name']}")
                
                rate_limiter.wait()
                
            except Exception as e:
                continue
        
        if incorrect_tracks:
            print(f"   ❌ Found {len(incorrect_tracks)} incorrect tracks (sample):")
            for track in incorrect_tracks[:5]:  # Show first 5
                print(f"      - {track}")
            if len(incorrect_tracks) > 5:
                print(f"      ... and {len(incorrect_tracks) - 5} more")
            total_incorrect_tracks += len(incorrect_tracks)
        else:
            print(f"   ✅ No incorrect tracks found in sample")
    
    print(f"\n📊 Total incorrect tracks found in samples: {total_incorrect_tracks}")
    print("💡 Run the full cleanup to remove all incorrect tracks")

def main():
    """Main function"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--preview":
        preview_cleanup()
    else:
        cleanup_all_genre_playlists()

if __name__ == "__main__":
    main() 