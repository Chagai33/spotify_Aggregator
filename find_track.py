import os
import app

app.sp = app.spotipy.Spotify(auth_manager=app.SpotifyOAuth(scope="playlist-read-private playlist-read-collaborative", open_browser=False, cache_path=".spotifycachesl"))

print("Loading source playlists...")
source_playlists = app.load_source_playlists(app.sp)

print("Searching for 'Mas Que Nada' in source playlists...")
found = False
for plist in source_playlists:
    tracks = app.get_all_playlist_tracks(app.sp, plist['id'])
    for item in tracks:
        track_obj = item.get('track')
        if not track_obj:
            continue
        track_name = track_obj.get('name', '')
        if 'mas que nada' in track_name.lower():
            print(f"Found '{track_name}' in playlist: {plist.get('name')}")
            
            # Check description parsing
            desc = plist.get('description', '')
            print(f"  Description: {desc}")
            parsed = app.parse_description(desc)
            print(f"  Parsed Genres: {parsed}")
            
            if parsed:
                for mapping in parsed:
                    genre = mapping['genre']
                    target = app.REVERSE_ROUTING.get(genre.lower())
                    print(f"  Mapped Target (from description): {target}")

            is_isr, is_fuzzy = app.is_israeli_track(track_obj)
            print(f"  Is Israeli Track (from track metadata): {is_isr}, Fuzzy: {is_fuzzy}")
            if is_isr:
                for artist in track_obj.get('artists', []):
                    artist_name = artist.get('name', '')
                    if artist_name.strip().lower() in app.ISRAELI_ARTISTS_SET:
                        print(f"    Triggered by artist in SET: {artist_name}")
            print("-" * 40)
            found = True

if not found:
    print("Could not find 'Mas Que Nada' in any source playlist.")
