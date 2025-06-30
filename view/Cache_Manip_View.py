import streamlit as st
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from controller import Artist_Cacher, Update_Cache, Fix_Custom_Genres

st.title('Cache Manipulation')

# Get playlist ID from session state
playlist_id = st.session_state.get('playlist_id')

if playlist_id:
    st.info(f'🎵 Working with playlist ID: {playlist_id}')

# Navigation state
if 'cache_view' not in st.session_state:
    st.session_state.cache_view = 'main'

def show_main_menu():
    if st.button('Run Artist Cacher'):
        if playlist_id:
            try:
                Artist_Cacher.main(playlist_id)
                st.success('Artist cacher completed!')
            except Exception as e:
                st.error(f'Error running artist cacher: {str(e)}')
        else:
            st.error('❌ No playlist ID available. Please enter a valid Spotify playlist URL in the main configuration.')
    
    if st.button('Update Cache'):
        try:
            Update_Cache.main()
            st.success('Cache updated!')
        except Exception as e:
            st.error(f'Error updating cache: {str(e)}')
    
    if st.button('Fix Custom Genres'):
        if playlist_id:
            try:
                Fix_Custom_Genres.main(playlist_id)
                st.success('Custom genres fixed!')
            except Exception as e:
                st.error(f'Error fixing custom genres: {str(e)}')
        else:
            st.error('❌ No playlist ID available. Please enter a valid Spotify playlist URL in the main configuration.')
    
    if st.button('Manual Genre Inputs'):
        st.session_state.cache_view = 'manual_genre'
    if st.button('Manual Country Inputs'):
        st.session_state.cache_view = 'manual_country'

def show_manual_genre_inputs():
    from view import Manual_Genre_Inputs_View
    if st.button('Back to Cache Menu'):
        st.session_state.cache_view = 'main'
        st.experimental_rerun()
    else:
        Manual_Genre_Inputs_View  # The view runs on import

def show_manual_country_inputs():
    from view import Manual_Country_Inputs_View
    if st.button('Back to Cache Menu'):
        st.session_state.cache_view = 'main'
        st.experimental_rerun()
    else:
        Manual_Country_Inputs_View  # The view runs on import

if st.session_state.cache_view == 'main':
    show_main_menu()
elif st.session_state.cache_view == 'manual_genre':
    show_manual_genre_inputs()
elif st.session_state.cache_view == 'manual_country':
    show_manual_country_inputs()