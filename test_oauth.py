import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Load dotenv to ensure credentials are read
load_dotenv()

client_id = os.getenv("SPOTIPY_CLIENT_ID")
client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI")

print("--- CREDENTIALS CHECK ---")
print(f"ID Length: {len(client_id) if client_id else 0}")
print(f"Secret Length: {len(client_secret) if client_secret else 0}")
print(f"Redirect URI: {redirect_uri}")

print("\n--- SPOTIPY INITIATION ---")
try:
    scope = "playlist-read-private playlist-read-collaborative playlist-modify-public playlist-modify-private"
    sp_oauth = SpotifyOAuth(scope=scope, open_browser=False, cache_path=".spotifycachesl")
    
    token_info = sp_oauth.get_cached_token()
    if token_info:
        print("✅ Found an existing token in .spotifycachesl!")
        sp = spotipy.Spotify(auth_manager=sp_oauth)
        user = sp.current_user()
        print(f"Logged in automatically as: {user['display_name']} ({user['id']})")
    else:
        print("⚠️ No cached token. Auth flow required.")
except Exception as e:
    print(f"❌ OAuth Error: {e}")
