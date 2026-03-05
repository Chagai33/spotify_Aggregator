import re
import time
import pandas as pd
import streamlit as st
from config.settings import TARGET_PLAYLISTS, REVERSE_ROUTING, EXCLUSION_LIST
from utils.parser import parse_description
from utils.helpers import chunk_list, is_israeli_track
from core.spotify_client import get_all_playlist_tracks

@st.cache_data(show_spinner="Fetching target deduplication data...")
def load_target_existing_uris(_sp):
    existing = {}
    for target_name, target_id in TARGET_PLAYLISTS.items():
        tracks = get_all_playlist_tracks(_sp, target_id)
        uris = set()
        for item in tracks:
            t = item.get('track')
            if t and t.get('uri'):
                uris.add(t['uri'])
        existing[target_name] = uris
    return existing

def run_global_checksum(sp, all_source_playlists, force_refresh_id=None):
    if force_refresh_id and st.session_state["checksum_results"] is not None:
        # Targeted Refresh: Only update the specific row in the existing state
        for i, r in enumerate(st.session_state["checksum_results"]):
            if r["ID"] == force_refresh_id:
                try:
                    fresh_p = sp.playlist(force_refresh_id)
                    desc = fresh_p.get('description', '')
                except:
                    desc = r.get('Description', '')
                    
                parsed = parse_description(desc)
                if parsed is None:
                    st.session_state["checksum_results"][i].update({
                        "Description": desc, "Parsed Sum": "N/A", "Actual Tracks": r['Actual Tracks'], "Status": "❌ Missing Counts"
                    })
                else:
                    parsed_sum = sum(g['count'] for g in parsed)
                    actual_tracks = r['Actual Tracks']
                    status = "✅ OK" if parsed_sum == actual_tracks else "❌ Mismatch"
                    st.session_state["checksum_results"][i].update({
                        "Description": desc, "Parsed Sum": parsed_sum, "Actual Tracks": actual_tracks, "Status": status
                    })
        return

    # General Sweep: Runs completely from the local cache
    results = []
    for p in all_source_playlists:
        desc = p.get('description', '')
        parsed = parse_description(desc)
        
        if parsed is None:
            results.append({"ID": p['id'], "Playlist": p['name'], "Description": desc, "Parsed Sum": "N/A", "Actual Tracks": p['tracks']['total'], "Status": "❌ Missing Counts"})
        else:
            parsed_sum = sum(g['count'] for g in parsed)
            actual_tracks = p['tracks']['total']
            status = "✅ OK" if parsed_sum == actual_tracks else "❌ Mismatch"
            results.append({"ID": p['id'], "Playlist": p['name'], "Description": desc, "Parsed Sum": parsed_sum, "Actual Tracks": actual_tracks, "Status": status})
    
    st.session_state["checksum_results"] = results


def process_mapping(sp, batch_playlists, simulate_only=True):
    """Core logic to map tracks, handling simulation and execution states for a specific batch slice."""
    
    audit_log = []
    target_staged_tracks = {t: [] for t in TARGET_PLAYLISTS.keys()}
    
    global_anomalies = set()
    total_skipped = 0
    total_dropped = 0
    total_null = 0
    local_existing_uris = {k: set(v) for k,v in st.session_state['target_existing_uris'].items()}

    progress_text = "Simulating Mapping..." if simulate_only else "Executing Batch Migration..."
    progress_bar = st.progress(0, text=progress_text)
    
    if not batch_playlists:
        st.warning("No more playlists left to process.")
        return [], {}, set()
        
    for idx, playlist in enumerate(batch_playlists):
        progress_bar.progress((idx) / len(batch_playlists), text=f"{progress_text} ({idx+1}/{len(batch_playlists)})")
        
        plist_name = playlist['name']
        description = playlist.get('description', '')
        parsed_genres = parse_description(description)
        
        if parsed_genres is None:
            st.warning(f"Skipped '{plist_name}': Missing track counts in description.")
            audit_log.append({
                "Source Playlist": plist_name, 
                "Parsed Genre": "N/A", 
                "Target Playlist": "None", 
                "Track Name": "Playlist Skipped", 
                "Artist Name": "N/A",
                "Action Taken": "Skipped Playlist (Missing Info/Counts)",
                "Track URI": "None"
            })
            continue
            
        tracks = get_all_playlist_tracks(sp, playlist['id'])
        
        # Checksum Guard
        expected_count = sum(g['count'] for g in parsed_genres)
        if expected_count != len(tracks):
            st.warning(f"Checksum mismatch for '{plist_name}': expected {expected_count} tracks, but found {len(tracks)}.")
            audit_log.append({
                "Source Playlist": plist_name, 
                "Parsed Genre": "N/A", 
                "Target Playlist": "None", 
                "Track Name": "Checksum Mismatch", 
                "Artist Name": "N/A",
                "Action Taken": "Skipped Playlist (Checksum Mismatch)",
                "Track URI": "None"
            })
            continue
        
        track_index = 0
        for p_genre in parsed_genres:
            genre_name = p_genre['genre'].lower()
            count = p_genre['count']
            
            target = REVERSE_ROUTING.get(genre_name)
            is_excluded = genre_name in EXCLUSION_LIST
            
            if not target and not is_excluded:
                global_anomalies.add(genre_name)
                target = "s3 למיין"
                
            for _ in range(count):
                if track_index >= len(tracks):
                    break
                
                item = tracks[track_index]
                track_index += 1
                
                track_obj = item.get('track')
                if not track_obj or not track_obj.get('uri') or track_obj['uri'].startswith('spotify:local:'):
                    total_null += 1
                    track_name = track_obj.get('name', 'Unknown') if track_obj else 'Unknown Data'
                    artist_name = ", ".join([a.get('name', 'Unknown') for a in track_obj.get('artists', [])]) if track_obj and track_obj.get('artists') else 'Unknown'
                    audit_log.append({"Source Playlist": plist_name, "Parsed Genre": genre_name, "Target Playlist": "None", "Track Name": track_name, "Artist Name": artist_name, "Action Taken": "Skipped (Null URI)", "Track URI": "None"})
                    continue
                
                uri = track_obj['uri']
                track_name = track_obj.get('name', 'Unknown')
                artist_name = ", ".join([a.get('name', 'Unknown') for a in track_obj.get('artists', [])]) if track_obj.get('artists') else 'Unknown'
                
                if is_excluded:
                    total_dropped += 1
                    audit_log.append({"Source Playlist": plist_name, "Parsed Genre": genre_name, "Target Playlist": "Drop List", "Track Name": track_name, "Artist Name": artist_name, "Action Taken": "Dropped (Exclusion List)", "Track URI": uri})
                    continue
                    
                israeli_bonus_matched = False
                
                if target:
                    # Mutual Exclusion for Hip Hop
                    if target == "♩ Hip Hop, Rap" and uri in local_existing_uris.get("♩ Israeli Hip Hop", set()):
                        audit_log.append({"Source Playlist": plist_name, "Parsed Genre": genre_name, "Target Playlist": target, "Track Name": track_name, "Artist Name": artist_name, "Action Taken": "Skipped (Excluded Sub-genre)", "Track URI": uri})
                    elif uri in local_existing_uris[target]:
                        total_skipped += 1
                        audit_log.append({"Source Playlist": plist_name, "Parsed Genre": genre_name, "Target Playlist": target, "Track Name": track_name, "Artist Name": artist_name, "Action Taken": "Skipped Duplicate", "Track URI": uri})
                    else:
                        target_staged_tracks[target].append(uri)
                        local_existing_uris[target].add(uri)
                        audit_log.append({"Source Playlist": plist_name, "Parsed Genre": genre_name, "Target Playlist": target, "Track Name": track_name, "Artist Name": artist_name, "Action Taken": "Appended", "Track URI": uri})

                # --- Parallel Israeli Music Routing ---
                is_isr, is_fuzzy = is_israeli_track(track_obj)
                if target != "♩ Israeli Music" and is_isr:
                    israeli_target = "♩ Israeli Music"
                    
                    warning_flag = " ⚠️ Review" if is_fuzzy else ""

                    # Mutual Exclusion for Israeli Music
                    if target in ["♩ Mizrahi", "♩ Israeli Hip Hop"] or \
                       uri in local_existing_uris.get("♩ Mizrahi", set()) or \
                       uri in local_existing_uris.get("♩ Israeli Hip Hop", set()):
                        audit_log.append({"Source Playlist": plist_name, "Parsed Genre": genre_name, "Target Playlist": israeli_target, "Track Name": track_name, "Artist Name": artist_name, "Action Taken": f"Skipped (Excluded Sub-genre){warning_flag}", "Track URI": uri})
                    else:
                        israeli_bonus_matched = True
                        if uri in local_existing_uris[israeli_target]:
                            audit_log.append({"Source Playlist": plist_name, "Parsed Genre": genre_name, "Target Playlist": israeli_target, "Track Name": track_name, "Artist Name": artist_name, "Action Taken": f"Skipped Duplicate (Bonus: Israeli Music){warning_flag}", "Track URI": uri})
                        else:
                            target_staged_tracks[israeli_target].append(uri)
                            local_existing_uris[israeli_target].add(uri)
                            audit_log.append({"Source Playlist": plist_name, "Parsed Genre": genre_name, "Target Playlist": israeli_target, "Track Name": track_name, "Artist Name": artist_name, "Action Taken": f"Appended (Bonus: Israeli Music){warning_flag}", "Track URI": uri})
                        
                if not target and not israeli_bonus_matched:
                    audit_log.append({"Source Playlist": plist_name, "Parsed Genre": genre_name, "Target Playlist": "None", "Track Name": track_name, "Artist Name": artist_name, "Action Taken": "Unmapped / Ignored", "Track URI": uri})

    progress_bar.progress(1.0, text="Process Complete!")
    return audit_log, target_staged_tracks, global_anomalies


def render_tab1(sp, all_source_playlists):
    if 'target_existing_uris' not in st.session_state or not st.session_state['target_existing_uris']:
        st.session_state['target_existing_uris'] = load_target_existing_uris(sp)

    # 1. Visual Pre-Flight Check
    st.subheader("1. Identified Target Source Playlists")
    st.markdown("Playlists are correctly sorted chronologically by their `Week#`.")
    with st.expander("View Source Playlists", expanded=False):
        playlist_data = []
        for p in all_source_playlists:
            match = re.search(r'Week#(2[0-9]{2}|300)', p['name'])
            week_num = int(match.group(1)) if match else "Unknown" # Handle missing/invalid Week#
            playlist_data.append({
                "Week#": week_num, 
                "Name": p['name'], 
                "Tracks": p['tracks']['total'], 
                "Description": p.get('description', '')
            })
            
        df_sources = pd.DataFrame(playlist_data)
        st.dataframe(df_sources, use_container_width=True)
        
    # 2. Global Checksum Utility
    st.subheader("2. Global Checksum Utility")
    
    if "checksum_results" not in st.session_state:
        st.session_state["checksum_results"] = None
        
    with st.expander("Run Validation on All Playlists", expanded=True):
        if st.button("🔍 Run Global Checksum"):
            with st.spinner("Validating all playlists..."):
                run_global_checksum(sp, all_source_playlists)
                
        if st.session_state["checksum_results"] is not None:
            results = st.session_state["checksum_results"]
            mismatches = [r for r in results if r["Status"] != "✅ OK"]
            
            if mismatches:
                st.error(f"Found {len(mismatches)} mismatching/failing playlists that require attention!")
            else:
                st.success("All playlists perfectly match their described track counts!")
                
            # Display detailed view with refresh buttons
            st.markdown("### Checksum Details")
            for r in results:
                cols = st.columns([2, 4, 1, 1, 1.5, 1])
                cols[0].write(f"**{r['Playlist']}**")
                cols[1].caption(r['Description'] if r['Description'] else "*No Description*")
                cols[2].write(f"Parsed: {r['Parsed Sum']}")
                cols[3].write(f"Actual: {r['Actual Tracks']}")
                
                if r["Status"] == "✅ OK":
                    cols[4].success(r["Status"])
                else:
                    cols[4].error(r["Status"])
                    
                # Individual refresh button for this row
                if cols[5].button("🔄", key=f"refresh_{r['ID']}"):
                    with st.spinner(f"Refreshing {r['Playlist']}..."):
                        run_global_checksum(sp, all_source_playlists, force_refresh_id=r['ID'])
                        st.rerun()
            
            st.divider()

    # 3. Phase A: Batch Preview
    st.subheader("3. Phase A: Preview Batch Migration")
    
    remaining = len(all_source_playlists) - st.session_state['current_playlist_index']
    st.markdown(f"**Current Progress:** Processed `{st.session_state['current_playlist_index']}` out of `{len(all_source_playlists)}` playlists.")
    progress_val = st.session_state['current_playlist_index'] / len(all_source_playlists) if len(all_source_playlists) > 0 else 0
    st.progress(progress_val)
    
    if remaining > 0:
        c_back, c1, c2, c3, c4 = st.columns(5)
        batch_to_run = 0
        
        if c_back.button("⬅️ Go Back 5", disabled=(st.session_state['current_playlist_index'] == 0)):
             st.session_state['current_playlist_index'] = max(0, st.session_state['current_playlist_index'] - 5)
             st.rerun()

        if c1.button("Preview Next 5", disabled=(remaining==0)):
            batch_to_run = min(5, remaining)
        if c2.button("Preview Next 10", disabled=(remaining==0)):
            batch_to_run = min(10, remaining)
        if c3.button("Preview All Remaining", disabled=(remaining==0)):
            batch_to_run = remaining
            
        if c4.button("🔁 Reset Progress", type="secondary"):
             st.session_state['current_playlist_index'] = 0
             st.session_state['pending_preview'] = []
             st.session_state['pending_staged'] = {}
             st.session_state['pending_batch_size'] = 0
             st.session_state['pending_anomalies'] = set()
             st.warning("Progress reset. You can now start over.")
             time.sleep(1.5)
             st.rerun()
            
        if batch_to_run > 0:
            with st.spinner(f"Simulating Batch ({batch_to_run} playlists)..."):
                start_idx = st.session_state["current_playlist_index"]
                end_idx = min(start_idx + batch_to_run, len(all_source_playlists))
                b_playlists = all_source_playlists[start_idx:end_idx]
                
                batch_log, staged_tracks, full_anomalies = process_mapping(sp, b_playlists, simulate_only=True)
                
                # Store pending preview results in session state
                st.session_state['pending_preview'] = batch_log
                st.session_state['pending_staged'] = staged_tracks
                st.session_state['pending_anomalies'] = full_anomalies
                st.session_state['pending_batch_size'] = batch_to_run
                st.session_state['pending_mode'] = 'batch'
                st.rerun()
                
    else:
        st.success("All playlists have been completely migrated!")
        if st.button("🔁 Reset Progress", type="secondary"):
             st.session_state['current_playlist_index'] = 0
             st.session_state['pending_preview'] = []
             st.session_state['pending_staged'] = {}
             st.session_state['pending_batch_size'] = 0
             st.session_state['pending_anomalies'] = set()
             st.rerun()

    st.divider()
    st.subheader("3b. Process Specific Playlist")
    st.markdown("Run a single target out-of-order.")
    
    playlist_options = [f"[{i}] {p['name']}" for i, p in enumerate(all_source_playlists)]
    selected_option = st.selectbox("Select Target Source:", playlist_options)
    
    if st.button("Preview Single Target"):
        idx_selected = int(selected_option.split(']')[0][1:])
        selected_playlist = all_source_playlists[idx_selected]
        
        with st.spinner(f"Simulating '{selected_playlist['name']}'..."):
            batch_log, staged_tracks, full_anomalies = process_mapping(sp, [selected_playlist], simulate_only=True)
            st.session_state['pending_preview'] = batch_log
            st.session_state['pending_staged'] = staged_tracks
            st.session_state['pending_anomalies'] = full_anomalies
            st.session_state['pending_batch_size'] = 1
            st.session_state['pending_mode'] = 'single'
            st.session_state['pending_single_playlist'] = selected_playlist
            st.rerun()

    # If we have a pending preview staged, display the Dataframe and Execution buttons
    if st.session_state['pending_preview'] and st.session_state['pending_batch_size'] > 0:
        st.divider()
        st.subheader("Preview (Action Required)")
        sim_df = pd.DataFrame(st.session_state['pending_preview'])
        st.dataframe(sim_df, use_container_width=True)
        
        if st.session_state['pending_anomalies']:
            st.warning(f"Unmapped Genres Detected: {', '.join(st.session_state['pending_anomalies'])}")
            
        st.subheader("4. Phase B: Execute Batch")
        
        col_ok, col_refresh, col_cancel = st.columns([2, 2, 4])
        
        with col_ok:
            if st.button("✅ Confirm & Push to Spotify", type="primary"):
                staged_tracks = st.session_state['pending_staged']
                batch_run = st.session_state['pending_batch_size']
                mode = st.session_state.get('pending_mode', 'batch')
                
                with st.status(f"Uploading Tracks...", expanded=True) as status:
                    chunks_done = 0
                    for target_name, uris in staged_tracks.items():
                        if not uris:
                            continue
                        target_id = TARGET_PLAYLISTS[target_name]
                        st.write(f"Pushing {len(uris)} new tracks to `{target_name}`...")
                        for chunk in chunk_list(uris, 100):
                            sp.playlist_add_items(target_id, chunk)
                            chunks_done += 1
                            time.sleep(0.5)
                    status.update(label="Upload Complete!", state="complete", expanded=False)
                
                # Update cumulative State
                if mode == 'batch':
                    start_num = st.session_state["current_playlist_index"]
                    st.session_state["current_playlist_index"] += batch_run
                    msg = f"Successfully processed playlists index {start_num} through {start_num + batch_run - 1}!"
                else:
                    msg = "Successfully processed single out-of-order playlist!"
                    
                st.session_state["cumulative_audit_log"].extend(st.session_state['pending_preview'])
                
                # Update local URIs so the next batch knows about the tracks we just appended
                for tgt, uris in staged_tracks.items():
                    st.session_state['target_existing_uris'][tgt].update(uris)
                    
                # Clear pending states safely
                st.session_state['pending_preview'] = []
                st.session_state['pending_staged'] = {}
                st.session_state['pending_batch_size'] = 0
                st.session_state['pending_anomalies'] = set()
                
                st.success(msg)
                time.sleep(1.5)
                st.rerun()
                
        with col_refresh:
            if st.button("🔄 Refresh Preview"):
                mode = st.session_state.get('pending_mode', 'batch')
                if mode == 'batch':
                    batch_to_run = st.session_state['pending_batch_size']
                    start_idx = st.session_state["current_playlist_index"]
                    end_idx = min(start_idx + batch_to_run, len(all_source_playlists))
                    b_playlists = all_source_playlists[start_idx:end_idx]
                else:
                    b_playlists = [st.session_state['pending_single_playlist']]
                    
                with st.spinner("Simulating again..."):
                    batch_log, staged_tracks, full_anomalies = process_mapping(sp, b_playlists, simulate_only=True)
                    st.session_state['pending_preview'] = batch_log
                    st.session_state['pending_staged'] = staged_tracks
                    st.session_state['pending_anomalies'] = full_anomalies
                    st.rerun()

        with col_cancel:
            if st.button("❌ Cancel Batch"):
                st.session_state['pending_preview'] = []
                st.session_state['pending_staged'] = {}
                st.session_state['pending_batch_size'] = 0
                st.session_state['pending_anomalies'] = set()
                st.rerun()
    
    # 4. Phase C: Cumulative CSV Reporting
    st.divider()
    st.subheader("4. Cumulative Audit Log")
    
    cumulative_log = st.session_state["cumulative_audit_log"]
    if cumulative_log:
        final_df = pd.DataFrame(cumulative_log)
        st.dataframe(final_df.tail(100), use_container_width=True)
        st.caption("Showing last 100 entries of the cumulative run...")
        
        csv = final_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Cumulative Audit Log (CSV)",
            data=csv,
            file_name='spotify_migration_audit_log.csv',
            mime='text/csv',
            type="primary"
        )
    else:
        st.info("No batches executed yet. The cumulative audit log is empty.")
