import streamlit as st
from model.Genre_Tools import load_artist_cache, save_artist_cache, get_artist_name_from_cache

st.title('Manual Country Input')

def get_artists_without_country(artist_cache):
    return [aid for aid, data in artist_cache.items() if data.get('country') is None]

if 'country_artist_cache' not in st.session_state:
    st.session_state.country_artist_cache = load_artist_cache()
    st.session_state.country_artists = get_artists_without_country(st.session_state.country_artist_cache)
    st.session_state.country_index = 0
    st.session_state.country_processed = 0
    st.session_state.country_skipped = 0

artists = st.session_state.country_artists
cache = st.session_state.country_artist_cache
idx = st.session_state.country_index

if idx < len(artists):
    artist_id = artists[idx]
    artist_name = get_artist_name_from_cache(artist_id, cache)
    genres = cache[artist_id].get('genres', [])
    st.write(f"**Artist:** {artist_name}")
    st.write(f"**Spotify ID:** {artist_id}")
    st.write(f"**Genres:** {', '.join(genres) if genres else 'None'}")
    country_input = st.text_input("Enter country for this artist:", key=f"country_{idx}")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Country", key=f"save_country_{idx}"):
            if country_input:
                cache[artist_id]['country'] = country_input
                save_artist_cache(cache)
                st.session_state.country_processed += 1
                st.session_state.country_index += 1
                st.success(f"Saved country: {country_input}")
                st.experimental_rerun()
    with col2:
        if st.button("Skip", key=f"skip_country_{idx}"):
            st.session_state.country_skipped += 1
            st.session_state.country_index += 1
            st.info("Skipped.")
            st.experimental_rerun()
    st.write(f"Progress: {idx+1} / {len(artists)}")
else:
    st.success(f"All artists processed! Processed: {st.session_state.country_processed}, Skipped: {st.session_state.country_skipped}") 