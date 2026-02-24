import re
import time
import json
import unicodedata
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration Definitions ---
TARGET_PLAYLISTS = {
    "Israeli Hip Hop": "1Ycl9i5uMtniDKs0jKvJOe",
    "Reggae": "3obWJRscGGN4QvmeLZK7US",
    "Israeli Music": "70y6Euzv1eUaYgR6Qzoo2r",
    "Country, Indie": "6QZz84AaYPlD1ALgrVacP4",
    "Melodic House": "7F8Bea5phhXrDwAx5rETPg",
    "Hip Hop, Rap": "3GiWLHwdkZU9VQ4i1aagWa",
    "Afrobeats": "1XyXp1FRHBRnvxmmhT5Sz6",
    "Mizrahi": "1zcEZURYYKMCvs4rpTB6ti",
    "Reggaeton": "09QZH7Nlj4vS9Paur6Srcm"
}

GENRE_ROUTING_DICT = {
    "Israeli Hip Hop": ["Israeli Hip Hop", "Israeli Rap"],
    "Reggae": ["Reggae", "Modern Reggae", "Reggae Rock", "Indie Reggae", "West Coast Reggae"],
    "Israeli Music": ["Israeli Music", "Israeli Pop", "Israeli Indie", "Indie IL"],
    "Country, Indie": ["Country", "Country Pop", "Indie", "Indie Pop", "American Indie", "Indie Folk", "Pop, Folk", "Folk, Pop", "Indie Soul", "Soul Indie", "Retro soul", "Modern Indie Folk", "Modern Indie", "Indie Rock", "Alternative Indie", "Alternative Pop", "Acoustic Soul", "Folk Acoustic", "Folk-Soul", "Pop Soul", "Lo-Fi", "R And B", "Rendb", "RB", "Meditation", "Chill Indie", "Spacial Intro", "Electro Chil", "Indie Modern Funk"],
    "Melodic House": ["Melodic House", "Melodic Techno", "Tropical House", "Organic House", "Indie House", "Tech House", "Techno House", "Bass House", "Base House", "Funky Bass House", "Edm", "EDM House", "Electro House", "Funky House", "Fusion House", "Electropop", "Brazilian Edm", "Mix House", "Groove House", "House", "Mix Gener", "Mix", "Groove Metal"],
    "Hip Hop, Rap": ["Hip Hop", "Rap", "Hip Hop, Rap", "Rap, Hip Hop", "UG Hip Hop", "Underground Hip Hop", "UG Hip Pop", "Trap", "Dark Trap", "Latin Trap", "Bass Trap", "Hip Pop", "East Coast Hip Hop", "Multigenre Rap", "Dfw Rap", "London Rap", "Westcoast Rap", "West Coast Rap", "Drift Phonk", "Kenyan Drill", "Hip Hop Rap"],
    "Afrobeats": ["Afrobeats", "Afrobeat", "Dancehall"],
    "Mizrahi": ["Mizrahi", "Mizrachi", "Yemeni Diwan"],
    "Reggaeton": ["Reggaeton", "Reggaton"]
}

EXCLUSION_LIST = [g.lower() for g in ["Drum N Base", "Drum N Bass", "DrumNBase", "Uk Dnb", "Dubstep", "Psytrance"]]

# Pre-process routing dictionary for O(1) case-insensitive lookup
REVERSE_ROUTING = {}
for target, genres in GENRE_ROUTING_DICT.items():
    for g in genres:
        REVERSE_ROUTING[g.lower()] = target

# --- Helper Functions ---

def parse_description(description):
    """Parses description to extract ordered genres and track counts."""
    if not description:
        return []
    
    # Unicode Normalization (converts superscripts like ⁴ to 4, 𝐼𝑠𝑟𝑎𝑒𝑙𝑖 to Israeli)
    text = unicodedata.normalize('NFKC', description)
    
    # Tokenize by the ♩ symbol
    segments = text.split('♩')
    
    # Backup mapping just in case NFKC didn't catch specific superscript numerals
    superscripts = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")
    
    parsed = []
    for segment in segments:
        segment = segment.strip()
        if not segment:
            continue
        
        # Match text ending in digits for the count
        match = re.search(r'^(.*?)\s*([\d⁰¹²³⁴⁵⁶⁷⁸⁹]+)$', segment)
        if match:
            genre_name = match.group(1).strip().strip('/').strip()
            count_str = match.group(2).translate(superscripts)
            try:
                count = int(count_str)
                parsed.append({"genre": genre_name, "count": count})
            except ValueError:
                pass
    return parsed

def get_all_user_playlists(sp):
    """Fetches ALL user playlists with pagination to bypass folder limitations."""
    playlists = []
    offset = 0
    while True:
        results = sp.current_user_playlists(limit=50, offset=offset)
        if not results['items']:
            break
        playlists.extend(results['items'])
        if len(results['items']) < 50:
            break
        offset += len(results['items'])
    return playlists

def get_target_source_playlists(all_playlists):
    """Filters all playlists to find the 97 target source ones (Aum#201-297)."""
    pattern = re.compile(r'Aum#(20[1-9]|2[1-8][0-9]|29[0-7])')
    matched = []
    for p in all_playlists:
        # p can be None in some rare Spotify API responses
        if p and p.get('name') and pattern.search(p['name']):
            matched.append(p)
    # Sort them by name just to ensure deterministic execution order
    matched.sort(key=lambda x: x['name'])
    return matched

def get_all_playlist_tracks(sp, playlist_id):
    """Fetches ALL tracks from a playlist, handling pagination."""
    tracks = []
    offset = 0
    while True:
        results = sp.playlist_items(playlist_id, limit=100, offset=offset)
        if not results['items']:
            break
        tracks.extend(results['items'])
        if len(results['items']) < 100:
            break
        offset += len(results['items'])
    return tracks

def chunk_list(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

# --- Main Logic ---

def main():
    scope = "playlist-read-private playlist-read-collaborative playlist-modify-public playlist-modify-private"
    print("Authenticating with Spotify...")
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

    print("Fetching ALL user playlists from Spotify API...")
    all_playlists = get_all_user_playlists(sp)
    print(f"-> Total playlists loaded into memory: {len(all_playlists)}")
    
    source_playlists = get_target_source_playlists(all_playlists)
    print(f"-> Filtered down to {len(source_playlists)} target source playlists (Aum#...).")
    
    print("\nIdentified Source Playlists:")
    for i, p in enumerate(source_playlists, 1):
        print(f"  {i}. {p['name']}")
    
    if not source_playlists:
        print("No source playlists found matching the criteria. Exiting.")
        return

    print("\nFetching current Target Playlist tracks for deep deduplication...")
    target_existing_uris = {}
    for target_name, target_id in TARGET_PLAYLISTS.items():
        tracks = get_all_playlist_tracks(sp, target_id)
        uris = set()
        for item in tracks:
            # Null/Local check for existing items too
            if item and item.get('track') and item['track'].get('uri'):
                uris.add(item['track']['uri'])
        target_existing_uris[target_name] = uris
        print(f" -> '{target_name}': {len(uris)} existing tracks.")

    # Execution State
    global_anomalies = set()
    target_staged_tracks = {target: [] for target in TARGET_PLAYLISTS.keys()}
    
    total_processed = 0
    total_skipped_dup = 0
    total_excluded = 0
    
    print("\n==================================")
    print("        BEGIN METADATA MAP        ")
    print("==================================")
    
    for idx, playlist in enumerate(source_playlists):
        # Human in the Loop Dry-Run Logic
        is_dry_run_limit_reached = (idx == 2)
        if is_dry_run_limit_reached:
            ans = input("\n[DRY-RUN] Processed 2 playlists. Do you approve this mapping to proceed with the remaining playlists and push to Spotify? (y/n): ")
            if ans.lower() != 'y':
                print("Execution aborted by user.")
                return
            print("\nResuming execution for the remaining playlists...")
        
        plist_name = playlist['name']
        description = playlist.get('description', '')
        
        parsed_genres = parse_description(description)
        
        print(f"\n--- Processing [{idx+1}/{len(source_playlists)}]: {plist_name} ---")
        
        # Build mapping plan
        track_index = 0
        skipped_dup = 0
        excluded = 0
        unmapped = 0
        null_uris = 0
        mapped_to_target = {t: 0 for t in TARGET_PLAYLISTS.keys()}
        
        tracks = get_all_playlist_tracks(sp, playlist['id'])
        
        for p_genre in parsed_genres:
            genre_name = p_genre['genre'].lower()
            count = p_genre['count']
            
            # Identify routing target
            target = REVERSE_ROUTING.get(genre_name)
            
            # Validate exclusion
            is_excluded = genre_name in EXCLUSION_LIST
            if not target and not is_excluded:
                global_anomalies.add(genre_name)
                unmapped += count
                
            for _ in range(count):
                if track_index >= len(tracks):
                    break # Reached the end of available tracks before count fulfilled
                
                item = tracks[track_index]
                track_index += 1
                
                # Strict Null Check
                track_obj = item.get('track')
                if not track_obj or not track_obj.get('uri'):
                    null_uris += 1
                    continue
                
                uri = track_obj['uri']
                
                if is_excluded:
                    excluded += 1
                    continue
                    
                if target:
                    # Deduplication check against existing and already staged tracks
                    if uri in target_existing_uris[target]:
                        skipped_dup += 1
                    else:
                        target_staged_tracks[target].append(uri)
                        target_existing_uris[target].add(uri) # Update local dict to prevent intra-run dups
                        mapped_to_target[target] += 1
        
        # Console output for this playlist mapping
        mapped_output = False
        for t, c in mapped_to_target.items():
            if c > 0:
                print(f"  -> {t}: +{c} tracks")
                mapped_output = True
        
        if not mapped_output and not skipped_dup and not excluded and not unmapped and not null_uris:
            print("  -> No mappings found. Potentially missing '♩' description format.")
            
        if skipped_dup > 0:
            print(f"  [!] Skipped {skipped_dup} exact duplicates.")
        if excluded > 0:
            print(f"  [x] Dropped {excluded} tracks (Exclusion List).")
        if unmapped > 0:
            print(f"  [?] {unmapped} tracks had unrecognized genre assignments.")
        if null_uris > 0:
            print(f"  [-] {null_uris} tracks lacked valid Spotify URIs (Skipped safely).")
        
        total_processed += 1
        total_skipped_dup += skipped_dup
        total_excluded += excluded

    # After full mapping approval and extraction, push to Spotify
    print("\n==================================")
    print("      STARTING BATCH API PUSH     ")
    print("==================================")
    for target, uris in target_staged_tracks.items():
        if not uris:
            continue
        print(f"Pushing {len(uris)} new tracks to {target}...")
        target_id = TARGET_PLAYLISTS[target]
        for chunk in chunk_list(uris, 100):
            # POST request appending tracks
            # Utilizing Spotipy's playlist_add_items which maps to the add_tracks API
            sp.playlist_add_items(target_id, chunk)
            time.sleep(0.5) # Gentle rate-limiting

    # Final summary report
    print("\n======== FINAL SUMMARY REPORT ========")
    print(f"Total Source Playlists Processed: {total_processed}")
    print("\nTotal Tracks Routed (Successfully Appended):")
    total_routed = 0
    for target, uris in target_staged_tracks.items():
        count = len(uris)
        total_routed += count
        if count > 0:
            print(f"  - {target}: {count}")
    print(f"\nTotal Duplicate Tracks Skipped: {total_skipped_dup}")
    print(f"Total Tracks Excluded (Drop List): {total_excluded}")
    
    if global_anomalies:
        print("\nAnomalies (Genres processed but unmapped):")
        for a in global_anomalies:
            print(f"  - '{a}'")
    else:
        print("\nAnomalies: None detected! All parsed genres resolved cleanly.")

if __name__ == '__main__':
    main()
