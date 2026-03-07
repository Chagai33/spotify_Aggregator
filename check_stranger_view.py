import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Load API keys
load_dotenv()

# Authenticate as an APP (not a user) - this mimics a 100% complete stranger!
client_credentials_manager = SpotifyClientCredentials()
sp_stranger = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

# Your User ID (from earlier logs)
user_id = "fbszxf6omus5ze8x3uaawd5d6"

print(f"--- Fetching Public Playlists for User: {user_id} ---")
print("Authenticating as an anonymous guest/stranger...")

public_playlists = []
try:
    results = sp_stranger.user_playlists(user_id)
    public_playlists.extend(results['items'])
    
    while results['next']:
        results = sp_stranger.next(results)
        public_playlists.extend(results['items'])
        
    print(f"\n✅ Total Public Playlists Found: {len(public_playlists)}")
    print("-" * 50)
    
    for i, p in enumerate(public_playlists):
        # Even as a stranger, Spotify API returns these basic details for public lists
        print(f"{i+1}. {p['name']} (ID: {p['id']})")
        
except Exception as e:
    print(f"\n❌ Error fetching playlists: {e}")
