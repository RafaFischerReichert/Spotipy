import streamlit as st
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from controller import Playlist_Creator

st.title('Playlist Creation')

if st.button('Create Genre Playlists'):
    Playlist_Creator.create_genre_playlists_optimized()
    st.success('Genre playlists created!')

if st.button('Other Playlist Function (example)'):
    # Add other Playlist_Creator functions as needed
    st.info('Other playlist function executed.') 