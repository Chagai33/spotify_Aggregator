import os
import re
import time
import json
import spotipy
import streamlit as st
from config.settings import AUDIO_FEATURES_CACHE

def get_all_user_playlists(_sp):
    """Fetches ALL user playlists with pagination to bypass 1000+ limits. Includes safety limits."""
    playlists = []
    offset = 0
    max_fetches = 100 # Safety limit: max 5000 playlists
    fetches = 0
    
    while fetches < max_fetches:
        try:
            results = _sp.current_user_playlists(limit=50, offset=offset)
            if not results or not results.get('items'):
                break
            playlists.extend(results['items'])
            if len(results['items']) < 50:
                break
            offset += len(results['items'])
            fetches += 1
        except spotipy.SpotifyException as e:
            if e.http_status == 429:
                st.error("⛔ Spotify Rate Limit Reached! (Error 429: Too Many Requests). Spotify has temporarily blocked this application's access. Please wait before refreshing.")
                st.stop()
            else:
                st.error(f"Spotify API Error fetching playlists: {e}")
                st.stop()
        except Exception as e:
            st.error(f"Error fetching playlists at offset {offset}: {e}")
            st.stop()
            
    return playlists


def get_target_source_playlists(all_playlists):
    """Filters all playlists to find the target source ones (Week#200-300) and sorts them numerically."""
    # Matches Week# followed by 200 up to 300
    pattern = re.compile(r'Week#(2[0-9]{2}|300)')
    matched = []
    for p in all_playlists:
        if p and p.get('name') and pattern.search(p['name']):
            # Extract number for precise sorting
            num = int(pattern.search(p['name']).group(1))
            matched.append((num, p))
            
    # Sort by the extracted Week# number
    matched.sort(key=lambda x: x[0])
    return [p for num, p in matched]


def fetch_audio_features_with_cache(_sp, uris):
    """
    Fetches audio features for a list of URIs. uses a local JSON cache to avoid rate limits.
    Spotify limits audio_features to 100 URIs per request.
    """
    if not uris:
        return {}
        
    cache_path = AUDIO_FEATURES_CACHE
    cache_data = {}
    
    # 1. Load existing cache
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
        except Exception:
            cache_data = {}
            
    # 2. Identify missing URIs
    missing_uris = [uri for uri in uris if uri not in cache_data]
    
    # 3. Fetch missing URIs in batches of 100
    if missing_uris:
        # Deduplicate to prevent API errors
        missing_uris = list(set(missing_uris)) 
        
        for i in range(0, len(missing_uris), 100):
            batch = missing_uris[i:i+100]
            try:
                features = _sp.audio_features(batch)
                
                # Zip and update cache
                for uri, feature in zip(batch, features):
                    if feature: # Sometimes spotify returns None for local files
                        cache_data[uri] = {
                            "energy": feature.get("energy", 0.5),
                            "key": feature.get("key", 0),
                            "mode": feature.get("mode", 1)
                        }
                    else:
                        # Dummy fallback to prevent repeated API calls
                        cache_data[uri] = {"energy": 0.5, "key": 0, "mode": 1}
                        
            except Exception as e:
                st.error(f"Error fetching audio features: {e}")
                
        # 4. Save updated cache back to disk
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=4)
        except Exception:
            pass
            
    # 5. Build and return the requested sub-dictionary
    result = {uri: cache_data.get(uri) for uri in uris if uri in cache_data}
    return result


def get_all_playlist_tracks(_sp, playlist_id):
    """Fetches ALL tracks from a playlist, handling pagination and preventing hard loops."""
    tracks = []
    offset = 0
    max_fetches = 100 # Safety limit: Max 10,000 tracks per playlist
    fetches = 0
    
    while fetches < max_fetches:
        try:
            results = _sp.playlist_items(playlist_id, limit=100, offset=offset)
            if not results or not results.get('items'):
                break
            tracks.extend(results['items'])
            if len(results['items']) < 100:
                break
            offset += len(results['items'])
            fetches += 1
        except spotipy.exceptions.SpotifyException as e:
            # Handle specific Spotify API errors (e.g., 404, rate limits)
            print(f"Spotify API Error fetching tracks for {playlist_id} at offset {offset}: {e}")
            break
        except Exception as e:
            print(f"Unexpected error fetching tracks for {playlist_id} at offset {offset}: {e}")
            break
            
    return tracks
