import streamlit as st
from model.Genre_Tools import load_artist_cache, save_artist_cache, get_artist_name_from_cache
from model.Artist_Genres import search_artist_by_name, extract_artist_id_from_url
from model.spotify_client import get_artist_with_retry

def update_tracks_for_artist(artist_id, artist_genres, cache):
    artist_name = get_artist_name_from_cache(artist_id, cache)
    cache[artist_id] = {
        'name': artist_name,
        'genres': artist_genres,
        'country': cache.get(artist_id, {}).get('country')
    }
    save_artist_cache(cache)
    return artist_name

def show_artist_genres(artist_id, cache):
    try:
        artist_name = get_artist_name_from_cache(artist_id, cache)
        if artist_id not in cache or not cache[artist_id].get('genres'):
            artist = get_artist_with_retry(artist_id)
            artist_name = artist['name']
            cache[artist_id] = {
                'name': artist_name,
                'genres': artist.get('genres', []),
                'country': cache.get(artist_id, {}).get('country')
            }
            save_artist_cache(cache)
        genres = cache[artist_id].get('genres', [])
        st.write(f"**Artist:** {artist_name}")
        st.write(f"**Spotify ID:** {artist_id}")
        st.write(f"**Genres:** {', '.join(genres) if genres else 'None'}")
        if not genres:
            genres_input = st.text_input("Enter genres (comma-separated):", key=f"manual_{artist_id}")
            if st.button("Save Genres", key=f"save_{artist_id}"):
                manual_genres = [g.strip() for g in genres_input.split(',') if g.strip()]
                if manual_genres:
                    update_tracks_for_artist(artist_id, manual_genres, cache)
                    st.success(f"Added manual genres: {', '.join(manual_genres)}")
                    st.experimental_rerun()
    except Exception as e:
        st.error(f"Error getting artist data: {str(e)}")

def artist_checker_view():
    st.title('Artist Checker')
    if 'artist_cache' not in st.session_state:
        st.session_state.artist_cache = load_artist_cache()
    cache = st.session_state.artist_cache
    if 'artist_checker_menu' not in st.session_state:
        st.session_state.artist_checker_menu = 'menu'
    st.header('Artist Checker Menu')
    if st.session_state.artist_checker_menu == 'menu':
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button('Check artist ID by name'):
                st.session_state.artist_checker_menu = 'by_name'
                st.experimental_rerun()
        with col2:
            if st.button('Check artist genres by Spotify URL'):
                st.session_state.artist_checker_menu = 'by_url'
                st.experimental_rerun()
        with col3:
            if st.button('Check artist genres by artist code (ID)'):
                st.session_state.artist_checker_menu = 'by_id'
                st.experimental_rerun()
    elif st.session_state.artist_checker_menu == 'by_name':
        if st.button('Back to Menu'):
            st.session_state.artist_checker_menu = 'menu'
            st.experimental_rerun()
        artist_name = st.text_input('Enter artist name:')
        if st.button('Search by Name') and artist_name.strip():
            results = search_artist_by_name(artist_name.strip())
            if not results:
                st.error('No artists found')
            else:
                options = [f"{a['name']} ({a['id']})" for a in results]
                selected = st.selectbox('Select artist:', options)
                idx = options.index(selected)
                artist_id = results[idx]['id']
                show_artist_genres(artist_id, cache)
    elif st.session_state.artist_checker_menu == 'by_url':
        if st.button('Back to Menu'):
            st.session_state.artist_checker_menu = 'menu'
            st.experimental_rerun()
        url = st.text_input('Enter Spotify artist URL:')
        if st.button('Search by URL') and url.strip():
            try:
                artist_id = extract_artist_id_from_url(url.strip())
                show_artist_genres(artist_id, cache)
            except Exception as e:
                st.error(f"Error: {e}")
    elif st.session_state.artist_checker_menu == 'by_id':
        if st.button('Back to Menu'):
            st.session_state.artist_checker_menu = 'menu'
            st.experimental_rerun()
        artist_id = st.text_input('Enter Spotify artist ID:')
        if st.button('Search by ID') and artist_id.strip():
            show_artist_genres(artist_id.strip(), cache)

artist_checker_view() 