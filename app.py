import streamlit as st
import importlib
import sys
import os

st.set_page_config(page_title='Spotipy App', layout='centered')

st.title('Spotipy Control Panel')

# Import the URL extraction function
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'model')))
from Playlist_Tools import extract_playlist_id_from_url

# Navigation state
if 'main_view' not in st.session_state:
    st.session_state.main_view = 'menu'

# Playlist URL input at the top level
st.header('Playlist Configuration')
playlist_url = st.text_input(
    'Enter Spotify Playlist URL',
    placeholder='https://open.spotify.com/playlist/4GQhO4MTpS8iDanLQ4vcKW?si=a500f459aba34f74',
    help='Paste the full Spotify playlist URL here'
)

# Extract playlist ID and store in session state
if playlist_url:
    try:
        playlist_id = extract_playlist_id_from_url(playlist_url)
        st.session_state.playlist_id = playlist_id
        st.success(f'✅ Playlist ID extracted: {playlist_id}')
    except ValueError as e:
        st.error(f'❌ {str(e)}')
        st.session_state.playlist_id = None
else:
    st.session_state.playlist_id = None

# Show warning if no playlist ID is available
if not st.session_state.playlist_id:
    st.warning('⚠️ Please enter a valid Spotify playlist URL to use the tools.')

st.header('Main Menu')

# Show current playlist ID if available
if st.session_state.playlist_id:
    st.success(f'🎵 Current playlist: {st.session_state.playlist_id}')

def show_main_menu():
    col1, col2 = st.columns(2)
    with col1:
        if st.button('Playlist Tools'):
            st.session_state.main_view = 'playlist'
    with col2:
        if st.button('Cache Manipulation'):
            st.session_state.main_view = 'cache'
    if st.button('Check API Status'):
        spec = importlib.util.spec_from_file_location('check_api_status', os.path.join('controller', 'check_api_status.py'))
        check_api_status = importlib.util.module_from_spec(spec)
        sys.modules['check_api_status'] = check_api_status
        spec.loader.exec_module(check_api_status)
        result = check_api_status.check_api_status_str()
        if 'rate limit' in result.lower() or '❌' in result:
            st.error(result)
        elif 'api is working' in result.lower() or '✅' in result:
            st.success(result)
        else:
            st.info(result)
    if st.button('Artist Checker'):
        st.session_state.main_view = 'artist_checker'

if st.session_state.main_view == 'menu':
    show_main_menu()
elif st.session_state.main_view == 'playlist':
    if st.button('Back to Main Menu'):
        st.session_state.main_view = 'menu'
        st.experimental_rerun()
    else:
        spec = importlib.util.spec_from_file_location('Playlist_Tools_View', os.path.join('view', 'Playlist_Tools_View.py'))
        Playlist_Tools_View = importlib.util.module_from_spec(spec)
        sys.modules['Playlist_Tools_View'] = Playlist_Tools_View
        spec.loader.exec_module(Playlist_Tools_View)
elif st.session_state.main_view == 'cache':
    if st.button('Back to Main Menu'):
        st.session_state.main_view = 'menu'
        st.experimental_rerun()
    else:
        spec = importlib.util.spec_from_file_location('Cache_Manip_View', os.path.join('view', 'Cache_Manip_View.py'))
        Cache_Manip_View = importlib.util.module_from_spec(spec)
        sys.modules['Cache_Manip_View'] = Cache_Manip_View
        spec.loader.exec_module(Cache_Manip_View)
elif st.session_state.main_view == 'artist_checker':
    if st.button('Back to Main Menu'):
        st.session_state.main_view = 'menu'
        st.experimental_rerun()
    else:
        spec = importlib.util.spec_from_file_location('Artist_Checker_View', os.path.join('view', 'Artist_Checker_View.py'))
        Artist_Checker_View = importlib.util.module_from_spec(spec)
        sys.modules['Artist_Checker_View'] = Artist_Checker_View
        spec.loader.exec_module(Artist_Checker_View) 