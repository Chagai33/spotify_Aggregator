import os
import json
import time
import html
import pandas as pd
import streamlit as st
from core.spotify_client import get_all_user_playlists

def render_tab4(sp):
    st.header("📊 Phase 4: Global Playlists Insights")
    st.markdown("View comprehensive statistics for all your playlists. Since fetching follower counts for hundreds of playlists takes time, use 'Basic Sync' for a quick overview or 'Deep Refresh' for specific items.")
    
    STATS_FILE = "playlist_insights_cache.json"
    
    # Load cache from file if it exists and session state is empty
    if 'all_playlists_stats' not in st.session_state:
        if os.path.exists(STATS_FILE):
            try:
                with open(STATS_FILE, 'r', encoding='utf-8') as f:
                    st.session_state['all_playlists_stats'] = json.load(f)
            except Exception:
                st.session_state['all_playlists_stats'] = {}
        else:
            st.session_state['all_playlists_stats'] = {}
        
    col_basic, col_deep = st.columns(2)
    with col_basic:
        if st.button("⚡ Fast Sync (All Playlists, No Followers)", type="primary"):
            with st.spinner("Fetching basic playlist metadata..."):
                all_pls = get_all_user_playlists(sp)
                new_stats = {}
                for p in all_pls:
                    # Keep existing follower count if we already fetched it deeply, else 'N/A'
                    existing = st.session_state['all_playlists_stats'].get(p['id'], {})
                    followers = existing.get("Followers", "N/A")
                    
                    new_stats[p['id']] = {
                        "ID": p['id'],
                        "Playlist Name": p['name'],
                        "Followers": followers,
                        "Total Tracks": p['tracks']['total'],
                        "Public": "Yes" if p['public'] else "No",
                        "Collaborative": "Yes" if p['collaborative'] else "No",
                        "Description": html.unescape(p.get('description', '') or ''),
                        "Owner": p['owner']['display_name']
                    }
                st.session_state['all_playlists_stats'] = new_stats
                
                # Save to disk
                with open(STATS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(new_stats, f, indent=2, ensure_ascii=False)
                    
                st.success(f"Successfully loaded and cached {len(new_stats)} playlists!")
                time.sleep(1)
                st.rerun()

    with col_deep:
        if st.button("🐢 Deep Sync (All Playlists + Followers - VERY SLOW)"):
            if not st.session_state['all_playlists_stats']:
                st.warning("Please do a 'Fast Sync' first to load the playlist IDs.")
            else:
                total_pls = len(st.session_state['all_playlists_stats'])
                progress_bar = st.progress(0, text="Deep syncing all playlists...")
                
                for idx, (p_id, stats) in enumerate(st.session_state['all_playlists_stats'].items()):
                    try:
                        p_full = sp.playlist(p_id)
                        stats["Followers"] = p_full['followers']['total']
                        stats["Total Tracks"] = p_full['tracks']['total']
                        stats["Public"] = "Yes" if p_full['public'] else "No"
                        stats["Collaborative"] = "Yes" if p_full['collaborative'] else "No"
                        stats["Description"] = html.unescape(p_full.get('description', '') or '')
                        stats["Owner"] = p_full['owner']['display_name']
                        
                        # Polite API rate limiting
                        time.sleep(0.2)
                    except Exception:
                        stats["Followers"] = "Error"
                        time.sleep(1) # Back off on error
                    
                    progress_bar.progress((idx + 1) / total_pls, text=f"Deep syncing... ({idx + 1}/{total_pls})")
                
                # Save to disk after full deep sync
                with open(STATS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(st.session_state['all_playlists_stats'], f, indent=2, ensure_ascii=False)
                    
                progress_bar.empty()
                st.success("Deep sync complete! Insights cached locally.")
                time.sleep(1)
                st.rerun()

    st.divider()
    
    if st.session_state['all_playlists_stats']:
        st.subheader("Targeted Refresh")
        # Ensure we have a mapping from name -> id for the selectbox
        # We append the ID to handle if playlists have identical names
        name_to_id = {f"{v['Playlist Name']} ({k[:8]})": k for k, v in st.session_state['all_playlists_stats'].items()}
        selected_name = st.selectbox("Search and select a specific playlist to Deep Refresh:", options=list(name_to_id.keys()))
        
        if st.button("🔄 Deep Refresh Selected"):
            selected_id = name_to_id[selected_name]
            with st.spinner(f"Fetching full metadata..."):
                try:
                    p_full = sp.playlist(selected_id)
                    st.session_state['all_playlists_stats'][selected_id].update({
                        "Followers": p_full['followers']['total'],
                        "Total Tracks": p_full['tracks']['total'],
                        "Public": "Yes" if p_full['public'] else "No",
                        "Collaborative": "Yes" if p_full['collaborative'] else "No",
                        "Description": html.unescape(p_full.get('description', '') or ''),
                        "Owner": p_full['owner']['display_name']
                    })
                    
                    # Save to disk after individual update
                    with open(STATS_FILE, 'w', encoding='utf-8') as f:
                        json.dump(st.session_state['all_playlists_stats'], f, indent=2, ensure_ascii=False)
                        
                    st.success("Updated successfully, and cache saved!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to refresh: {e}")
                    
        st.divider()
        
        st.subheader("Playlists View")
        search_query = st.text_input("🔍 Filter Table by Playlist Name:").strip().lower()
        
        df_data = list(st.session_state['all_playlists_stats'].values())
        if search_query:
            df_data = [d for d in df_data if search_query in str(d["Playlist Name"]).lower()]
            
        if df_data:
            df = pd.DataFrame(df_data)
            df_display = df.drop(columns=["ID"]) if "ID" in df.columns else df
            st.dataframe(df_display, use_container_width=True)
            st.caption(f"Showing {len(df_data)} playlists.")
        else:
            st.info("No playlists match your search.")
    else:
        st.info("Click 'Fast Sync' above to load your playlists.")
