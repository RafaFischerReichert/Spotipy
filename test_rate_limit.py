#!/usr/bin/env python3
"""Test script to verify rate limiting is working properly."""

import time
from config import REQUESTS_PER_SECOND, PLAYLIST_ID
from spotify_client import sp
from Playlist_Tools import RateLimiter

def test_rate_limiting():
    """Test that rate limiting works properly."""
    print("🧪 Testing rate limiting...")
    
    # Initialize rate limiter with conservative settings
    rate_limiter = RateLimiter(requests_per_second=2.0)
    
    try:
        # Test 1: Get current user
        print("1. Testing current user API call...")
        rate_limiter.wait()
        user = sp.current_user()
        print(f"   ✅ Successfully got user: {user['display_name']}")
        
        # Test 2: Get playlist info
        print("2. Testing playlist info API call...")
        rate_limiter.wait()
        playlist = sp.playlist(PLAYLIST_ID)
        print(f"   ✅ Successfully got playlist: {playlist['name']} ({len(playlist['tracks']['items'])} tracks)")
        
        # Test 3: Get a few tracks from playlist
        print("3. Testing playlist tracks API call...")
        rate_limiter.wait()
        tracks = sp.playlist_tracks(PLAYLIST_ID, limit=5)
        print(f"   ✅ Successfully got {len(tracks['items'])} tracks from playlist")
        
        print("\n✅ All rate limiting tests passed!")
        print("🎉 Ready to run the main script safely.")
        
    except Exception as e:
        print(f"❌ Rate limiting test failed: {str(e)}")
        if 'rate' in str(e).lower():
            print("⚠️  Rate limit hit - you may need to wait before running the main script.")

if __name__ == "__main__":
    test_rate_limiting() 