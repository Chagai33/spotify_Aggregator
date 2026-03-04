import logging
import time
import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_fetch():
    print("Loading .env...")
    load_dotenv('.env')
    
    scope = "playlist-modify-public playlist-modify-private playlist-read-private playlist-read-collaborative"
    sp_oauth = SpotifyOAuth(scope=scope, open_browser=False, cache_path=".spotifycachesl")
    sp = spotipy.Spotify(auth_manager=sp_oauth, requests_timeout=5, retries=3)
    
    print("Attempting to fetch 1 playlist to test network/rate limits...")
    start = time.time()
    try:
        res = sp.current_user_playlists(limit=1, offset=0)
        print(f"Success! Fetched in {time.time() - start:.2f} seconds.")
        print(f"Total playlists reported by API: {res.get('total')}")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_fetch()
