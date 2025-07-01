"""Creates genre playlists from a source playlist.

This module creates genre playlists from a source playlist, using optimized 
batch processing and caching. Minimizes API calls and speeds up playlist 
creation by batching and checking for existing playlists.
"""

import time
from typing import Dict, List, Set, Any
from model.config import PLAYLIST_ID, REQUESTS_PER_SECOND
from model.Playlist_Tools import (
    get_existing_playlists,
    get_playlist_track_ids,
    create_genre_playlists,
    sp,
    RateLimiter
)
import streamlit as st

def create_genre_playlists_optimized(playlist_id: str) -> None:
    """Create genre playlists with optimized batch processing and caching (read-only cache)."""
    rate_limiter = RateLimiter(requests_per_second=REQUESTS_PER_SECOND)
    progress_bar = st.progress(0, text="Processing tracks...")
    cancelled = False
    def progress_callback(current, total):
        progress_bar.progress(current / total, text=f"Processing tracks... {current}/{total}")
        if 'cancel_playlist_creation' in st.session_state and st.session_state.cancel_playlist_creation:
            raise RuntimeError('Playlist creation cancelled by user.')
    try:
        genre_tracks = create_genre_playlists(playlist_id, progress_callback=progress_callback)
    except RuntimeError as e:
        progress_bar.empty()
        st.warning(str(e))
        return
    progress_bar.progress(1.0, text="Tracks processed!")
    existing_playlists: Dict[str, str] = get_existing_playlists()
    playlists_to_create = []
    playlists_to_update = []
    for genre, track_ids in genre_tracks.items():
        if len(track_ids) < 100:
            continue
        playlist_name: str = f"{genre.title()}"
        if playlist_name in existing_playlists:
            playlists_to_update.append((playlist_name, existing_playlists[playlist_name], track_ids))
        else:
            playlists_to_create.append((playlist_name, track_ids))
    if playlists_to_create:
        st.write(f"\nCreating {len(playlists_to_create)} new playlists...")
        user_id = sp.current_user()['id']
        for playlist_name, track_ids in playlists_to_create:
            if 'cancel_playlist_creation' in st.session_state and st.session_state.cancel_playlist_creation:
                st.warning('Playlist creation cancelled by user.')
                return
            try:
                playlist: Dict[str, Any] = sp.user_playlist_create(
                    user=user_id,
                    name=playlist_name,
                    public=True
                )
                playlist_id: str = playlist['id']
                st.write(f"Created new playlist '{playlist_name}'")
                track_ids_list: List[str] = list(track_ids)
                for i in range(0, len(track_ids_list), 50):
                    if 'cancel_playlist_creation' in st.session_state and st.session_state.cancel_playlist_creation:
                        st.warning('Playlist creation cancelled by user.')
                        return
                    chunk: List[str] = track_ids_list[i:i + 50]
                    sp.playlist_add_items(playlist_id, chunk)
                    rate_limiter.wait()
                st.write(f"Added {len(track_ids)} tracks to '{playlist_name}'")
                rate_limiter.wait()
            except Exception as e:
                st.error(f"Error creating playlist for {genre}: {str(e)}")
                time.sleep(5)
                continue
    if playlists_to_update:
        st.write(f"\nUpdating {len(playlists_to_update)} existing playlists...")
        for playlist_name, playlist_id, track_ids in playlists_to_update:
            if 'cancel_playlist_creation' in st.session_state and st.session_state.cancel_playlist_creation:
                st.warning('Playlist creation cancelled by user.')
                return
            try:
                st.write(f"Checking existing tracks in '{playlist_name}'...")
                existing_tracks: Set[str] = get_playlist_track_ids(playlist_id)
                new_track_ids = track_ids - existing_tracks
                if new_track_ids:
                    st.write(f"Adding {len(new_track_ids)} new tracks to '{playlist_name}'...")
                    track_ids_list: List[str] = list(new_track_ids)
                    for i in range(0, len(track_ids_list), 50):
                        if 'cancel_playlist_creation' in st.session_state and st.session_state.cancel_playlist_creation:
                            st.warning('Playlist creation cancelled by user.')
                            return
                        chunk: List[str] = track_ids_list[i:i + 50]
                        sp.playlist_add_items(playlist_id, chunk)
                        rate_limiter.wait()
                    st.write(f"Added {len(new_track_ids)} tracks to '{playlist_name}'")
                else:
                    st.write(f"No new tracks to add to '{playlist_name}'")
            except Exception as e:
                st.error(f"Error updating playlist for {genre}: {str(e)}")
                time.sleep(5)
                continue

if __name__ == "__main__":
    create_genre_playlists_optimized(PLAYLIST_ID)