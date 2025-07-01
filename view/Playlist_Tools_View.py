import streamlit as st
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from controller import Playlist_Creator, Fix_Custom_Genres, Genre_Lister, Genre_Ranker

st.title('Playlist Tools')

# Get playlist ID from session state
playlist_id = st.session_state.get('playlist_id')

if playlist_id:
    st.info(f'🎵 Working with playlist ID: {playlist_id}')
    
    # Cancel button logic
    if 'cancel_playlist_creation' not in st.session_state:
        st.session_state.cancel_playlist_creation = False
    if st.button('Cancel Playlist Creation'):
        st.session_state.cancel_playlist_creation = True
        st.warning('Playlist creation will be cancelled at the next opportunity.')
    
    # Create Genre Playlists
    if st.button('Create Genre Playlists'):
        st.session_state.cancel_playlist_creation = False
        try:
            Playlist_Creator.create_genre_playlists_optimized(playlist_id)
            st.success('Genre playlists created!')
        except Exception as e:
            st.error(f'Error creating genre playlists: {str(e)}')

    # Fix Custom Genres
    if st.button('Fix Custom Genres'):
        try:
            Fix_Custom_Genres.main(playlist_id)
            st.success('Custom genres fixed and playlists updated!')
        except Exception as e:
            st.error(f'Error fixing custom genres: {str(e)}')

    # List Genres
    if st.button('List All Genres'):
        try:
            Genre_Lister.list_playlist_genres(playlist_id)
            st.success('Genre listing completed!')
        except Exception as e:
            st.error(f'Error listing genres: {str(e)}')

    # Rank Genres
    if st.button('Rank Genres by Frequency'):
        try:
            Genre_Ranker.rank_playlist_genres(playlist_id)
            st.success('Genre ranking completed!')
        except Exception as e:
            st.error(f'Error ranking genres: {str(e)}')
else:
    st.error('❌ No playlist ID available. Please enter a valid Spotify playlist URL in the main configuration.') 