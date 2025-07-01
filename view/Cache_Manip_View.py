import streamlit as st
import sys
import os
import importlib
import threading
import queue
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Force reload of modules to clear cache
import controller.Artist_Cacher
import controller.Update_Cache
import controller.Fix_Custom_Genres
importlib.reload(controller.Artist_Cacher)
importlib.reload(controller.Update_Cache)
importlib.reload(controller.Fix_Custom_Genres)

from controller import Artist_Cacher, Update_Cache, Fix_Custom_Genres

st.title('Cache Manipulation')

# Get playlist ID from session state
playlist_id = st.session_state.get('playlist_id')

if playlist_id:
    st.info(f'🎵 Working with playlist ID: {playlist_id}')

# Navigation state
if 'cache_view' not in st.session_state:
    st.session_state.cache_view = 'main'

# Threading state
if 'cache_thread' not in st.session_state:
    st.session_state.cache_thread = None
if 'cancel_flag' not in st.session_state:
    st.session_state.cancel_flag = False
if 'operation_status' not in st.session_state:
    st.session_state.operation_status = None

def run_artist_cacher(playlist_id, progress_queue, error_queue):
    """Run artist cacher in a separate thread."""
    try:
        def progress_callback(value):
            progress_queue.put(value)
            if st.session_state.cancel_flag:
                raise Exception("Operation cancelled by user")
        
        Artist_Cacher.main(playlist_id, progress_callback=progress_callback)
        progress_queue.put(1.0)
    except Exception as e:
        error_queue.put(str(e))

def run_update_cache(progress_queue, error_queue):
    """Run update cache in a separate thread."""
    try:
        def progress_callback(value):
            progress_queue.put(value)
            if st.session_state.cancel_flag:
                raise Exception("Operation cancelled by user")
        
        Update_Cache.main(progress_callback=progress_callback)
        progress_queue.put(1.0)
    except Exception as e:
        error_queue.put(str(e))

def run_fix_custom_genres(playlist_id, progress_queue, error_queue):
    """Run fix custom genres in a separate thread."""
    try:
        def progress_callback(value):
            progress_queue.put(value)
            if st.session_state.cancel_flag:
                raise Exception("Operation cancelled by user")
        
        Fix_Custom_Genres.main(playlist_id, progress_callback=progress_callback)
        progress_queue.put(1.0)
    except Exception as e:
        error_queue.put(str(e))

def show_main_menu():
    # Cancel button (always visible)
    if st.button('🛑 Cancel Running Operation'):
        st.session_state.cancel_flag = True
        if st.session_state.cache_thread and st.session_state.cache_thread.is_alive():
            st.warning('Cancellation requested. Please wait for the operation to stop...')
        else:
            st.info('No operation currently running.')
        st.rerun()
    
    # Status display
    if st.session_state.operation_status:
        st.info(f"Status: {st.session_state.operation_status}")
    
    # Progress bar (if operation is running)
    if st.session_state.cache_thread and st.session_state.cache_thread.is_alive():
        progress_bar = st.progress(0)
        progress_placeholder = st.empty()
        
        # Update progress from queue
        try:
            progress_value = st.session_state.progress_queue.get_nowait()
            progress_bar.progress(min(max(progress_value, 0.0), 1.0))
            progress_placeholder.text(f"Progress: {progress_value:.1%}")
        except queue.Empty:
            pass
        
        # Check if thread is still running
        if not st.session_state.cache_thread.is_alive():
            # Operation completed
            try:
                error = st.session_state.error_queue.get_nowait()
                st.error(f'❌ Error: {error}')
                st.exception(Exception(error))
            except queue.Empty:
                st.success('✅ Operation completed successfully!')
            
            # Reset state
            st.session_state.cache_thread = None
            st.session_state.operation_status = None
            st.session_state.cancel_flag = False
            st.rerun()
    
    # Operation buttons
    if st.button('Run Artist Cacher'):
        if playlist_id:
            if st.session_state.cache_thread and st.session_state.cache_thread.is_alive():
                st.warning('Another operation is already running. Please wait or cancel it first.')
            else:
                # Reset state
                st.session_state.cancel_flag = False
                st.session_state.operation_status = "Running Artist Cacher..."
                st.session_state.progress_queue = queue.Queue()
                st.session_state.error_queue = queue.Queue()
                
                # Start thread
                st.session_state.cache_thread = threading.Thread(
                    target=run_artist_cacher,
                    args=(playlist_id, st.session_state.progress_queue, st.session_state.error_queue)
                )
                st.session_state.cache_thread.start()
                st.rerun()
        else:
            st.error('❌ No playlist ID available. Please enter a valid Spotify playlist URL in the main configuration.')
    
    if st.button('Update Cache'):
        if st.session_state.cache_thread and st.session_state.cache_thread.is_alive():
            st.warning('Another operation is already running. Please wait or cancel it first.')
        else:
            # Reset state
            st.session_state.cancel_flag = False
            st.session_state.operation_status = "Updating Cache..."
            st.session_state.progress_queue = queue.Queue()
            st.session_state.error_queue = queue.Queue()
            
            # Start thread
            st.session_state.cache_thread = threading.Thread(
                target=run_update_cache,
                args=(st.session_state.progress_queue, st.session_state.error_queue)
            )
            st.session_state.cache_thread.start()
            st.rerun()
    
    if st.button('Fix Custom Genres'):
        if playlist_id:
            if st.session_state.cache_thread and st.session_state.cache_thread.is_alive():
                st.warning('Another operation is already running. Please wait or cancel it first.')
            else:
                # Reset state
                st.session_state.cancel_flag = False
                st.session_state.operation_status = "Fixing Custom Genres..."
                st.session_state.progress_queue = queue.Queue()
                st.session_state.error_queue = queue.Queue()
                
                # Start thread
                st.session_state.cache_thread = threading.Thread(
                    target=run_fix_custom_genres,
                    args=(playlist_id, st.session_state.progress_queue, st.session_state.error_queue)
                )
                st.session_state.cache_thread.start()
                st.rerun()
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
        st.rerun()
    else:
        Manual_Genre_Inputs_View  # The view runs on import

def show_manual_country_inputs():
    from view import Manual_Country_Inputs_View
    if st.button('Back to Cache Menu'):
        st.session_state.cache_view = 'main'
        st.rerun()
    else:
        Manual_Country_Inputs_View  # The view runs on import

if st.session_state.cache_view == 'main':
    show_main_menu()
elif st.session_state.cache_view == 'manual_genre':
    show_manual_genre_inputs()
elif st.session_state.cache_view == 'manual_country':
    show_manual_country_inputs()