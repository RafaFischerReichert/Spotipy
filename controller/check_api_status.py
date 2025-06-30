"""Check Spotify API status and rate limit information."""

import time
import logging
import io
import sys
import threading
from contextlib import redirect_stdout, redirect_stderr
from model.spotify_client import sp

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

def check_api_status_str():
    """Check current API rate limit status and return output as a string."""
    output = io.StringIO()
    # Capture logging output to detect rate limit warnings
    log_capture = io.StringIO()
    log_handler = logging.StreamHandler(log_capture)
    logging.getLogger().addHandler(log_handler)
    logging.getLogger().setLevel(logging.WARNING)
    # Capture stdout and stderr to catch rate limit warnings
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    try:
        log_capture.truncate(0)
        log_capture.seek(0)
        stdout_capture.truncate(0)
        stdout_capture.seek(0)
        stderr_capture.truncate(0)
        stderr_capture.seek(0)
        print("=== Spotify API Status Check ===\n", file=output)
        print("Making API call...", file=output)
        start_time = time.time()
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            user = api_call_with_timeout(10)  # 10 second timeout
        end_time = time.time()
        print("API call completed!", file=output)
        log_output = log_capture.getvalue()
        stdout_output = stdout_capture.getvalue()
        stderr_output = stderr_capture.getvalue()
        print(f"Debug - Log output: {repr(log_output)}", file=output)
        print(f"Debug - Stdout output: {repr(stdout_output)}", file=output)
        print(f"Debug - Stderr output: {repr(stderr_output)}", file=output)
        all_output = (log_output + stdout_output + stderr_output).lower()
        if ('rate' in all_output and 'limit' in all_output) or '86400' in all_output:
            print("❌ Rate limit exceeded", file=output)
            print("The API client detected a rate limit and is waiting.", file=output)
            print("\nThis means you've made too many API calls in the past 24 hours.", file=output)
            print("The API client will automatically retry after the rate limit resets (86400 seconds = 24 hours).", file=output)
            print("\nTo avoid this in the future:", file=output)
            print("- Run scripts less frequently", file=output)
            print("- Use smaller batch sizes", file=output)
            print("- Add more delays between requests", file=output)
            if stderr_output.strip():
                print(f"\nWarning message: {stderr_output.strip()}", file=output)
        else:
            call_duration = end_time - start_time
            if call_duration > 5:
                print("⚠️  API call took unusually long time - may be rate limited", file=output)
                print(f"Call duration: {call_duration:.2f} seconds", file=output)
                print("The API client may be waiting for rate limit to reset.", file=output)
            else:
                print("✅ API is working - rate limit not exceeded", file=output)
                print(f"Current user: {user['display_name']}", file=output)
                print(f"API call duration: {call_duration:.2f} seconds", file=output)
    except TimeoutError as e:
        print(f"❌ {e}", file=output)
        print("This likely means the API is rate limited and the client is waiting.", file=output)
        print("The Spotify API client is probably in a wait() state.", file=output)
        print("\nTo check if you're rate limited:", file=output)
        print("1. Wait a few hours and try again", file=output)
        print("2. Check your Spotify Developer Dashboard for rate limit status", file=output)
        print("3. Consider reducing the frequency of your API calls", file=output)
    except Exception as e:
        error_msg = str(e).lower()
        if 'rate' in error_msg or 'limit' in error_msg:
            print("❌ Rate limit exceeded", file=output)
            print(f"Error: {e}", file=output)
            print("\nThis means you've made too many API calls in the past 24 hours.", file=output)
            print("You'll need to wait for the rate limit to reset (24-hour rolling window).", file=output)
            print("\nTo avoid this in the future:", file=output)
            print("- Run scripts less frequently", file=output)
            print("- Use smaller batch sizes", file=output)
            print("- Add more delays between requests", file=output)
        else:
            print(f"❌ Other error: {e}", file=output)
    finally:
        logging.getLogger().removeHandler(log_handler)
    print(f"\nCurrent time: {time.strftime('%Y-%m-%d %H:%M:%S')}", file=output)
    return output.getvalue()

def check_api_status():
    """Check current API rate limit status and print output (for CLI usage)."""
    print(check_api_status_str())

if __name__ == "__main__":
    check_api_status() 