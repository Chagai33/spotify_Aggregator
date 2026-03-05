import re
from config.settings import ISRAELI_ARTISTS_SET

def chunk_list(lst, n):
    """Yields successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def is_israeli_track(track_obj):
    """Determines if a track has Hebrew characters or an Israeli artist.
       Returns a tuple (is_israeli, is_fuzzy_match), where is_fuzzy_match 
       is True if matched only by English dictionary name."""
    if not track_obj:
        return False, False
        
    # Check track name for Hebrew characters
    track_name = track_obj.get('name', '')
    if re.search(r'[\u0590-\u05FF]', track_name):
        return True, False
        
    # Check artists
    artists = track_obj.get('artists', [])
    for artist in artists:
        artist_name = artist.get('name', '')
        if not artist_name:
            continue
            
        # Check artist name for Hebrew characters
        if re.search(r'[\u0590-\u05FF]', artist_name):
            return True, False
            
        # Check against parsed set 
        if artist_name.strip().lower() in ISRAELI_ARTISTS_SET:
            return True, True
            
    return False, False

def extract_playlist_id(input_str):
    """Extracts Spotify base-62 ID from standard Spotify URL or URI."""
    if not input_str: 
        return None
    match = re.search(r'playlist[:/]([a-zA-Z0-9]+)', input_str)
    return match.group(1) if match else input_str.strip()
