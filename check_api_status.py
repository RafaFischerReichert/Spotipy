"""Check Spotify API status and rate limit information."""

import time
import logging
import io
import sys
import threading
from contextlib import redirect_stdout, redirect_stderr
from spotify_client import sp

class TimeoutError(Exception):
    pass

def api_call_with_timeout(timeout_seconds=10):
    """Make API call with timeout using threading."""
    result = [None]
    exception = [None]
    
    def make_call():
        try:
            result[0] = sp.current_user()
        except Exception as e:
            exception[0] = e
    
    thread = threading.Thread(target=make_call)
    thread.daemon = True
    thread.start()
    thread.join(timeout_seconds)
    
    if thread.is_alive():
        raise TimeoutError(f"API call timed out after {timeout_seconds} seconds")
    
    if exception[0]:
        raise exception[0]
    
    return result[0]

def check_api_status():
    """Check current API rate limit status.
    
    Displays information about the current Spotify API status, including
    whether the API is working and if rate limits have been exceeded.
    """
    print("=== Spotify API Status Check ===\n")
    
    # Capture logging output to detect rate limit warnings
    log_capture = io.StringIO()
    log_handler = logging.StreamHandler(log_capture)
    logging.getLogger().addHandler(log_handler)
    logging.getLogger().setLevel(logging.WARNING)
    
    # Capture stdout and stderr to catch rate limit warnings
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    
    try:
        # Clear any previous warnings
        log_capture.truncate(0)
        log_capture.seek(0)
        stdout_capture.truncate(0)
        stdout_capture.seek(0)
        stderr_capture.truncate(0)
        stderr_capture.seek(0)
        
        print("Making API call...")
        
        # Try a simple API call and measure the time
        start_time = time.time()
        
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            user = api_call_with_timeout(10)  # 10 second timeout
        
        end_time = time.time()
        
        print("API call completed!")
        
        # Check if any warnings were logged during the API call
        log_output = log_capture.getvalue()
        stdout_output = stdout_capture.getvalue()
        stderr_output = stderr_capture.getvalue()
        
        print(f"Debug - Log output: {repr(log_output)}")
        print(f"Debug - Stdout output: {repr(stdout_output)}")
        print(f"Debug - Stderr output: {repr(stderr_output)}")
        
        # Check for rate limit indicators in all captured output
        all_output = (log_output + stdout_output + stderr_output).lower()
        
        if ('rate' in all_output and 'limit' in all_output) or '86400' in all_output:
            print("❌ Rate limit exceeded")
            print("The API client detected a rate limit and is waiting.")
            print("\nThis means you've made too many API calls in the past 24 hours.")
            print("The API client will automatically retry after the rate limit resets (86400 seconds = 24 hours).")
            print("\nTo avoid this in the future:")
            print("- Run scripts less frequently")
            print("- Use smaller batch sizes")
            print("- Add more delays between requests")
            
            # Show the actual warning message if captured
            if stderr_output.strip():
                print(f"\nWarning message: {stderr_output.strip()}")
        else:
            # Check if the API call took an unusually long time (indicating rate limiting)
            call_duration = end_time - start_time
            if call_duration > 5:  # If it took more than 5 seconds, likely rate limited
                print("⚠️  API call took unusually long time - may be rate limited")
                print(f"Call duration: {call_duration:.2f} seconds")
                print("The API client may be waiting for rate limit to reset.")
            else:
                print("✅ API is working - rate limit not exceeded")
                print(f"Current user: {user['display_name']}")
                print(f"API call duration: {call_duration:.2f} seconds")
        
    except TimeoutError as e:
        print(f"❌ {e}")
        print("This likely means the API is rate limited and the client is waiting.")
        print("The Spotify API client is probably in a wait() state.")
        print("\nTo check if you're rate limited:")
        print("1. Wait a few hours and try again")
        print("2. Check your Spotify Developer Dashboard for rate limit status")
        print("3. Consider reducing the frequency of your API calls")
        
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
    
    finally:
        # Clean up logging handler
        logging.getLogger().removeHandler(log_handler)
    
    print(f"\nCurrent time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    check_api_status() 