import time
import pandas as pd
import streamlit as st
from utils.helpers import chunk_list
from core.spotify_client import get_all_playlist_tracks

def render_tab2(sp):
    st.header("🧹 Cross-Playlist Cleanup Utility")
    st.markdown("Safely remove tracks from **Playlist A** that already exist in **Playlist B**.")
    
    # Fetch all user playlists to populate dropdowns
    all_user_playlists = st.session_state.get('global_playlists', [])
    playlist_options = {p['name']: p['id'] for p in all_user_playlists}
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Playlist to Clean (Target A)")
        st.caption("Tracks will be deleted FROM this playlist.")
        a_dropdown = st.selectbox("Select Playlist A", options=list(playlist_options.keys()), key="cleanup_a_sel")
        from utils.helpers import extract_playlist_id
        a_url = st.text_input("Or enter Spotify URL for Playlist A", key="cleanup_a_url", placeholder="https://open.spotify.com/playlist/...")
        
    with col2:
        st.subheader("Reference Playlist (Target B)")
        st.caption("Tracks found HERE will be deleted from Target A.")
        b_dropdown = st.selectbox("Select Playlist B", options=list(playlist_options.keys()), key="cleanup_b_sel")
        b_url = st.text_input("Or enter Spotify URL for Playlist B", key="cleanup_b_url", placeholder="https://open.spotify.com/playlist/...")
        
    a_id = extract_playlist_id(a_url) or playlist_options.get(a_dropdown)
    b_id = extract_playlist_id(b_url) or playlist_options.get(b_dropdown)

    if st.button("🔍 Scan & Verify Overlap", type="primary"):
        if not a_id or not b_id:
            st.error("Invalid Playlist IDs.")
        elif a_id == b_id:
            st.error("Playlist A and Playlist B cannot be the same.")
        else:
            with st.spinner("Fetching tracks from both playlists..."):
                tracks_a = get_all_playlist_tracks(sp, a_id)
                tracks_b = get_all_playlist_tracks(sp, b_id)
                
                uris_b = {item['track']['uri'] for item in tracks_b if item.get('track') and item['track'].get('uri')}
                
                overlap = []
                uris_to_delete = []
                
                for item in tracks_a:
                    t = item.get('track')
                    if t and t.get('uri') and t['uri'] in uris_b:
                        overlap.append({
                            "Track Name": t.get('name', 'Unknown'),
                            "Artist": ", ".join(arr['name'] for arr in t.get('artists', [])),
                            "URI": t['uri']
                        })
                        if t['uri'] not in uris_to_delete: # Prevent duplicate URIs in the deletion array
                            uris_to_delete.append(t['uri'])
                        
                st.session_state['cleanup_uris'] = uris_to_delete
                st.session_state['cleanup_overlap'] = overlap
                st.session_state['cleanup_a_id'] = a_id
                
                if not overlap:
                    st.success("✅ No overlapping tracks found! Playlist A is fully independent of Playlist B.")
                
    if st.session_state.get('cleanup_uris'):
        st.divider()
        st.warning(f"Found {len(st.session_state['cleanup_uris'])} overlapping tracks ready for review.")
        
        # Build DataFrame and add the exclusion boolean column
        df_overlap = pd.DataFrame(st.session_state['cleanup_overlap'])
        if "Keep (Don't Delete)" not in df_overlap.columns:
            df_overlap.insert(0, "Keep (Don't Delete)", False)
            
        st.markdown("**Review the overlapping tracks below. Check the box if you want to KEEP the track in Playlist A.**")
        
        # Display as interactive data editor
        edited_df = st.data_editor(
            df_overlap,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Keep (Don't Delete)": st.column_config.CheckboxColumn(
                    "Keep (Don't Delete)",
                    help="Select this to protect the track from being deleted.",
                    default=False,
                )
            }
        )
        
        col_exec1, col_exec2 = st.columns([1, 4])
        
        # Filter URIs based on user selection in the data_editor
        final_uris_to_delete = edited_df[edited_df["Keep (Don't Delete)"] == False]["URI"].tolist()
        
        with col_exec1:
            if st.button(f"🗑️ Delete {len(final_uris_to_delete)} Tracks", type="primary"):
                if not final_uris_to_delete:
                    st.warning("No tracks selected for deletion (All tracks are marked to Keep).")
                else:
                    with st.spinner("Deleting selected tracks from Playlist A..."):
                        playlist_id_to_clean = st.session_state['cleanup_a_id']
                        
                        # Delete in chunks of 100
                        for chunk in chunk_list(final_uris_to_delete, 100):
                            sp.playlist_remove_all_occurrences_of_items(playlist_id_to_clean, chunk)
                            time.sleep(0.5)
                            
                    st.success(f"Successfully deleted {len(final_uris_to_delete)} overlapping tracks!")
                    
                st.session_state['cleanup_uris'] = []
                st.session_state['cleanup_overlap'] = []
                st.session_state['cleanup_a_id'] = None
                time.sleep(2)
                st.rerun()
                
        with col_exec2:
            if st.button("Cancel & Clear Settings"):
                st.session_state['cleanup_uris'] = []
                st.session_state['cleanup_overlap'] = []
                st.session_state['cleanup_a_id'] = None
                st.rerun()
