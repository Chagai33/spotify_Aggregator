import json
import time
from datetime import datetime
import pandas as pd
import streamlit as st
from config.settings import TARGET_PLAYLISTS
from utils.helpers import chunk_list
from core.spotify_client import get_all_playlist_tracks
from views.tab_1_migration import load_target_existing_uris

def render_tab3(sp):
    st.header("🛡️ Phase 3: Backup & Restore")
    st.markdown("Create snapshots of your target playlists before migrations, and restore them if necessary.")
    
    st.subheader("📦 Part 1: Create Snapshot (Backup)")
    if st.button("Create Target Playlists Snapshot", type="primary"):
        with st.spinner("Fetching current tracks from all target playlists..."):
            backup_data = {}
            for name, p_id in TARGET_PLAYLISTS.items():
                tracks = get_all_playlist_tracks(sp, p_id)
                # Keep only valid URIs
                uris = [item['track']['uri'] for item in tracks if item.get('track') and item['track'].get('uri') and not item['track']['uri'].startswith('spotify:local:')]
                backup_data[name] = uris
            
            json_str = json.dumps(backup_data, indent=2)
            date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"spotify_backup_{date_str}.json"
            
            st.success("Snapshot created successfully!")
            st.download_button(
                label=f"⬇️ Download {filename}",
                data=json_str,
                file_name=filename,
                mime="application/json"
            )
            
    st.divider()
    st.subheader("⚠️ Part 2: Restore from Snapshot (Rollback)")
    uploaded_file = st.file_uploader("Upload a backup JSON file", type=["json"])
    
    if uploaded_file is not None:
        try:
            restore_data = json.load(uploaded_file)
            st.write("Backup Contents:")
            
            # Display summary
            summary = [{"Playlist": k, "Tracks": len(v)} for k, v in restore_data.items()]
            st.dataframe(pd.DataFrame(summary), use_container_width=True)
            
            if st.button("⚠️ DANGER: Restore from Backup (Overwrite Current State)", type="primary"):
                with st.spinner("Restoring playlists..."):
                    for name, uris in restore_data.items():
                        if name not in TARGET_PLAYLISTS:
                            continue
                            
                        target_id = TARGET_PLAYLISTS[name]
                        st.write(f"Restoring `{name}` ({len(uris)} tracks)...")
                        
                        if not uris:
                            sp.playlist_replace_items(target_id, [])
                        else:
                            # Replace first 100 to clear existing and set first chunk
                            sp.playlist_replace_items(target_id, uris[:100])
                            time.sleep(0.5)
                            
                            # Add remaining tracks in chunks of 100
                            for chunk in chunk_list(uris[100:], 100):
                                sp.playlist_add_items(target_id, chunk)
                                time.sleep(0.5)
                                
                    # Reset session state caches to reflect restored state
                    st.session_state['target_existing_uris'] = load_target_existing_uris(sp)
                    st.success("Restore complete! All target playlists have been reverted to the backup state.")
                    time.sleep(2)
                    st.rerun()
                    
        except json.JSONDecodeError:
            st.error("Invalid JSON file uploaded.")
