import time
from spotify_client import sp

def check_api_status():
    """Check current API rate limit status"""
    print("=== Spotify API Status Check ===\n")
    
    try:
        # Try a simple API call to check rate limit
        user = sp.current_user()
        print("✅ API is working - rate limit not exceeded")
        print(f"Current user: {user['display_name']}")
        
    except Exception as e:
        error_msg = str(e).lower()
        if 'rate' in error_msg or 'limit' in error_msg:
            print("❌ Rate limit exceeded")
            print(f"Error: {e}")
            print("\nThis means you've made too many API calls in the past 24 hours.")
            print("You'll need to wait for the rate limit to reset (24-hour rolling window).")
            print("\nTo avoid this in the future:")
            print("- Run scripts less frequently")
            print("- Use smaller batch sizes")
            print("- Add more delays between requests")
        else:
            print(f"❌ Other error: {e}")
    
    print(f"\nCurrent time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    check_api_status() 