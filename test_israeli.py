import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import app

# Load environment variables (Client ID, Secret, Redirect URI)
load_dotenv()

scope = "playlist-read-private playlist-read-collaborative"
sp_oauth = SpotifyOAuth(scope=scope, open_browser=False, cache_path=".spotifycachesl")
sp = spotipy.Spotify(auth_manager=sp_oauth)

results = sp.search(q="Mas Que Nada", limit=5, type="track")
for track in results['tracks']['items']:
    print(f"Track: {track['name']}")
    for artist in track['artists']:
        print(f"  Artist: {artist['name']}")
    
    is_isr, is_fuzzy = app.is_israeli_track(track)
    print(f"  Is Israeli: {is_isr}, Fuzzy: {is_fuzzy}")
    
    if is_isr:
        for artist in track['artists']:
            artist_name = artist.get('name', '')
            if artist_name.strip().lower() in app.ISRAELI_ARTISTS_SET:
                print(f"  >>> Matched Artist in SET: '{artist_name}' (lower: '{artist_name.strip().lower()}')")
    print("-" * 40)
