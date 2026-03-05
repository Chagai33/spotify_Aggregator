import re
import time
import pandas as pd
import streamlit as st

from utils.helpers import chunk_list, extract_playlist_id
from core.spotify_client import get_all_playlist_tracks

def render_tab7(sp):
    st.header("🔍 Phase 7: Season Orphan Validator")
    st.markdown("Find and move tracks that infiltrated Master Playlists without being in any `Week#200-300` season playlists.")
    
    # State flags for Phase 7
    if "p7_orphans" not in st.session_state:
        st.session_state["p7_orphans"] = []
    if "p7_master_id" not in st.session_state:
        st.session_state["p7_master_id"] = None
    if "p7_dest_id" not in st.session_state:
        st.session_state["p7_dest_id"] = None
        
    all_user_playlists_p7 = st.session_state.get('global_playlists', [])
    playlist_options_p7 = {p['name']: p['id'] for p in all_user_playlists_p7}
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Master Playlist (To Clean)")
        st.caption("Select the official playlist to evaluate and clean.")
        master_dropdown = st.selectbox("Select Master Playlist", options=list(playlist_options_p7.keys()), key="p7_master_sel")
        master_url = st.text_input("Or enter Spotify URL for Master Playlist", key="p7_master_url", placeholder="https://open.spotify.com/playlist/...")
    
    with col2:
        st.subheader("Destination Playlist (Vault)")
        st.caption("Orphaned tracks will be moved here.")
        dest_dropdown = st.selectbox("Select Destination Playlist", options=list(playlist_options_p7.keys()), key="p7_dest_sel")
        dest_url = st.text_input("Or enter Spotify URL for Destination", key="p7_dest_url", placeholder="https://open.spotify.com/playlist/...")

    master_id = extract_playlist_id(master_url) or playlist_options_p7.get(master_dropdown)
    dest_id = extract_playlist_id(dest_url) or playlist_options_p7.get(dest_dropdown)
    
    if st.button("🔍 Scan & Verify Orphans", type="primary"):
        if not master_id or not dest_id:
            st.error("Invalid Playlist IDs.")
        elif master_id == dest_id:
            st.error("Master and Destination playlists cannot be the same.")
        else:
            with st.spinner("Fetching Season Source of Truth (Week#200-300)..."):
                # Fetch Playlist Names for UI Transparency (especially if URL was used)
                try:
                    master_name = sp.playlist(master_id)['name']
                    dest_name = sp.playlist(dest_id)['name']
                    st.info(f"**Targeting Master Playlist:** `{master_name}`")
                    st.info(f"**Moving Orphans To:** `{dest_name}`")
                except Exception as e:
                    st.error("Could not fetch playlist details. Make sure the URLs are public and valid.")
                    st.stop()
            
                # Check Cache First
                if "p7_season_uris" in st.session_state:
                    season_uris = st.session_state["p7_season_uris"]
                    st.success(f"Loaded Source of Truth from Memory Cache: {len(season_uris)} unique tracks.")
                else:    
                    # Find all season playlists
                    pattern = re.compile(r'Week#(2[0-9]{2}|300)')
                    season_playlists = [p for p in all_user_playlists_p7 if p and p.get('name') and pattern.search(p['name'])]
                    
                    if not season_playlists:
                        st.error("No season playlists (Week#...) found to build the Source of Truth.")
                        season_uris = set()
                    else:
                        season_uris = set()
                        # Aggregate ALL URIs from the season
                        progress_text = "Downloading Season Tracks. Please wait..."
                        my_bar = st.progress(0, text=progress_text)
                        
                        for i, p in enumerate(season_playlists):
                            tracks = get_all_playlist_tracks(sp, p['id'])
                            for item in tracks:
                                t = item.get('track')
                                if t and t.get('uri'):
                                    # Avoid adding Local Files to our truth source
                                    if not t['uri'].startswith('spotify:local:'):
                                        season_uris.add(t['uri'])
                            my_bar.progress((i + 1) / len(season_playlists), text=progress_text)
                        
                        # Save to Cache
                        st.session_state["p7_season_uris"] = season_uris
                        st.success(f"Built Source of Truth (And Cached for Session): {len(season_uris)} unique tracks found in Season.")
                
                if season_uris:
                    with st.spinner("Analyzing Master Playlist against Source of Truth..."):
                        master_tracks = get_all_playlist_tracks(sp, master_id)
                        orphans = []
                        orphan_uris = []
                        
                        for item in master_tracks:
                            t = item.get('track')
                            if not t or not t.get('uri'):
                                continue
                            
                            uri = t['uri']
                            # Skip local files completely, we can't move them easily anyway
                            if uri.startswith('spotify:local:'):
                                continue
                                
                            if uri not in season_uris:
                                orphans.append({
                                    "Track Name": t.get('name', 'Unknown'),
                                    "Artist": ", ".join(arr['name'] for arr in t.get('artists', [])),
                                    "Added At": item.get('added_at', 'Unknown'),
                                    "URI": uri
                                })
                                if uri not in orphan_uris:
                                    orphan_uris.append(uri)
                        
                        st.session_state["p7_orphans"] = orphans
                        st.session_state["p7_master_id"] = master_id
                        st.session_state["p7_dest_id"] = dest_id
                    
                        if not orphans:
                            st.success("✅ Perfect Architecture! 0 Orphans found. All tracks in the Master Playlist belong to this season.")

    if st.session_state.get("p7_orphans"):
        orphans = st.session_state["p7_orphans"]
        st.divider()
        st.warning(f"🚨 Found {len(orphans)} orphaned tracks! They are in the Master Playlist but were never in a weekly Release Radar.")
        
        st.dataframe(pd.DataFrame(orphans), use_container_width=True)
        
        col_exec1, col_exec2 = st.columns([1, 4])
        with col_exec1:
            if st.button(f"🚚 Move {len(orphans)} Tracks to Vault", type="primary"):
                with st.spinner("Moving Orphans safely..."):
                    uris_to_move = [o["URI"] for o in orphans]
                    source_id = st.session_state["p7_master_id"]
                    dest_vault_id = st.session_state["p7_dest_id"]
                    
                    # 1. Protection: Check what is already in the Vault so we don't duplicate
                    vault_tracks = get_all_playlist_tracks(sp, dest_vault_id)
                    vault_existing_uris = {item['track']['uri'] for item in vault_tracks if item.get('track') and item['track'].get('uri')}
                    
                    filtered_uris_to_add = [uri for uri in uris_to_move if uri not in vault_existing_uris]
                    
                    # 2. Add to Vault
                    if filtered_uris_to_add:
                        for chunk in chunk_list(filtered_uris_to_add, 100):
                            sp.playlist_add_items(dest_vault_id, chunk)
                            time.sleep(0.5)
                            
                    # 3. Remove cleanly from Master Playlist
                    for chunk in chunk_list(uris_to_move, 100):
                        sp.playlist_remove_all_occurrences_of_items(source_id, chunk)
                        time.sleep(0.5)
                        
                st.success(f"Execution Complete: {len(uris_to_move)} orphans were cleaned. {len(filtered_uris_to_add)} were added to the Vault (the rest were already there).")
                st.session_state["p7_orphans"] = []
                st.session_state["p7_master_id"] = None
                st.session_state["p7_dest_id"] = None
                time.sleep(3)
                st.rerun()
                
        with col_exec2:
            if st.button("❌ Cancel & Reset Tracker"):
                st.session_state["p7_orphans"] = []
                st.session_state["p7_master_id"] = None
                st.session_state["p7_dest_id"] = None
                st.rerun()
