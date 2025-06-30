import streamlit as st
from model.Genre_Tools import load_artist_cache, save_artist_cache, normalize_genre, deduplicate_hyphen_genres, get_artist_name_from_cache

def get_artists_without_genres(artist_cache):
    artists_without_genres = []
    generic_regional_genres = {"brazilian music", "japanese music"}
    for artist_id, data in artist_cache.items():
        genres = data.get('genres', [])
        if not genres:
            artists_without_genres.append(artist_id)
        elif len(genres) == 1 and genres[0].lower() in generic_regional_genres:
            artists_without_genres.append(artist_id)
    return artists_without_genres

st.title('Manual Genre Input')

if 'artist_cache' not in st.session_state:
    st.session_state.artist_cache = load_artist_cache()
    st.session_state.artists = get_artists_without_genres(st.session_state.artist_cache)
    st.session_state.current_index = 0
    st.session_state.processed = 0
    st.session_state.skipped = 0

artists = st.session_state.artists
cache = st.session_state.artist_cache
idx = st.session_state.current_index

if idx < len(artists):
    artist_id = artists[idx]
    artist_name = get_artist_name_from_cache(artist_id, cache)
    current_genres = cache.get(artist_id, {}).get('genres', [])
    st.write(f"**Artist:** {artist_name}")
    st.write(f"**Spotify ID:** {artist_id}")
    st.write(f"**Current genres:** {', '.join(current_genres) if current_genres else 'None'}")
    genres_input = st.text_input("Enter genres (comma-separated):", key=f"genres_{idx}")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Genres", key=f"save_{idx}"):
            genres = [g.strip() for g in genres_input.split(',') if g.strip()]
            normalized_genres = []
            for genre in genres:
                normalized_genres.extend(normalize_genre(genre))
            unique_genres = deduplicate_hyphen_genres(list(dict.fromkeys(normalized_genres)))
            cache[artist_id]['genres'] = unique_genres
            save_artist_cache(cache)
            st.session_state.processed += 1
            st.session_state.current_index += 1
            st.success(f"Saved genres: {', '.join(unique_genres)}")
            st.experimental_rerun()
    with col2:
        if st.button("Skip", key=f"skip_{idx}"):
            st.session_state.skipped += 1
            st.session_state.current_index += 1
            st.info("Skipped.")
            st.experimental_rerun()
    st.write(f"Progress: {idx+1} / {len(artists)}")
else:
    st.success(f"All artists processed! Processed: {st.session_state.processed}, Skipped: {st.session_state.skipped}") 