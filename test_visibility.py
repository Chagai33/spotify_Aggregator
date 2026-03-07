import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()

scope = "playlist-read-private playlist-read-collaborative playlist-modify-public playlist-modify-private"
sp_oauth = SpotifyOAuth(scope=scope, open_browser=False, cache_path=".spotifycachesl")
sp = spotipy.Spotify(auth_manager=sp_oauth)

# Use the same playlist ID to test reversing it to Private
playlist_id = "0yvOcmanGJES69KwZhKXsQ"

try:
    print("\nAttempting to make it PRIVATE via API...")
    sp.playlist_change_details(playlist_id, public=False)
    
    print("API Call executed. Checking Spotify immediately...")
    p_updated = sp.playlist(playlist_id)
    print(f"Verified Public Status direct from API: {p_updated['public']}")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
