import os
import json
import time
from datetime import datetime
import pandas as pd
import streamlit as st

from config.settings import TARGET_PLAYLISTS, CAMELOT_DICT
from utils.helpers import chunk_list
from core.spotify_client import get_all_playlist_tracks, fetch_audio_features_with_cache
from algorithms.sequencing import (
    apply_rollercoaster_wave_sort,
    apply_hit_interleave_sort,
    apply_csp_flow_sort,
    auto_select_sort
)

def render_tab5(sp):
    st.header("🌟 Phase 5: SEO & Popularity Optimizer")
    st.markdown("Analyze track popularity and optimize the top of your playlists to reduce skip rates. Advanced multi-year ranking algorithms combat 'recency bias'.")
    
    if 'seo_tracks' not in st.session_state:
        st.session_state['seo_tracks'] = []
    if 'seo_playlist_id' not in st.session_state:
        st.session_state['seo_playlist_id'] = None
    if 'seo_method' not in st.session_state:
        st.session_state['seo_method'] = "1. Spotify Native (Track Popularity Only)"
        
    st.subheader("1. Track Popularity Analyzer")
    col_seo1, col_seo2 = st.columns(2)
    with col_seo1:
        seo_target_name = st.selectbox("Select Master Playlist to Analyze:", options=list(TARGET_PLAYLISTS.keys()))
    with col_seo2:
        algo_choice = st.selectbox("Select Ranking Algorithm:", [
            "1. Spotify Native (Track Popularity Only) - Favors Hits",
            "2. Era Hybrid (Track 60% + Artist 40%) - Balanced",
            "3. Logarithmic Momentum (Track + Artist + Age) - Long Term"
        ], help="Approach 2 & 3 protect older hits from being buried by brand new mediocre tracks.")
    
    if st.button("🔍 Analyze Track Popularity"):
        selected_id = TARGET_PLAYLISTS[seo_target_name]
        with st.spinner("Fetching tracks, artist metrics, and release dates..."):
            tracks = get_all_playlist_tracks(sp, selected_id)
            
            # --- CURATOR OVERRIDE INIT ---
            favorites_playlist_id = "1X44CiyGrShr6ro8N1hGI6"
            try:
                st.info("Cross-referencing tracks against 'S3 My Favorite' for Curator Boosts...")
                f_tracks = get_all_playlist_tracks(sp, favorites_playlist_id)
                fav_uris = {item['track']['uri'] for item in f_tracks if item.get('track') and item['track'].get('uri')}
            except Exception as e:
                fav_uris = set()
                
            needs_advanced_metrics = "Native" not in algo_choice
            
            artist_cache = {}
            if needs_advanced_metrics:
                st.info("Advanced Algorithm selected: Fetching deep artist metrics...")
                
                # Setup Artist JSON Cache
                cache_file = "artist_popularity_cache.json"
                if os.path.exists(cache_file):
                    try:
                        with open(cache_file, "r") as f:
                            artist_cache = json.load(f)
                    except json.JSONDecodeError:
                        artist_cache = {}
                else:
                    artist_cache = {}
                    
                all_artist_ids = []
                for item in tracks:
                    t = item.get('track')
                    if t and t.get('artists') and t['artists'][0].get('id'):
                        all_artist_ids.append(t['artists'][0]['id']) # Just grab the primary artist
                
                unique_artist_ids = list(set([aid for aid in all_artist_ids if aid]))
                
                # Determine which artists are missing from the local JSON cache
                missing_artist_ids = [aid for aid in unique_artist_ids if aid not in artist_cache]
                cached_count = len(unique_artist_ids) - len(missing_artist_ids)
                
                if missing_artist_ids:
                    st.info(f"Targeting {len(unique_artist_ids)} unique artists. Loading {cached_count} from cache, fetching {len(missing_artist_ids)} new artists from Spotify API...")
                    # Fetch artist info in batches of 50 to respect rate limits
                    new_fetches = 0
                    for chunk in chunk_list(missing_artist_ids, 50):
                        try:
                            time.sleep(0.2) # Small safety delay
                            artists_data = sp.artists(chunk)
                            for a in artists_data['artists']:
                                if a:
                                    artist_cache[a['id']] = a['popularity']
                                    new_fetches += 1
                        except Exception as e:
                            print(f"Error fetching artist batch: {e}")
                            st.warning("Rate limit hit or API error on Artist fetch. Partial data used.")
                            
                    # Save updated cache to disk
                    if new_fetches > 0:
                        try:
                            with open(cache_file, "w") as f:
                                json.dump(artist_cache, f)
                        except Exception as e:
                            print(f"Failed to save artist cache: {e}")
                else:
                    st.success(f"All {len(unique_artist_ids)} unique artists loaded instantly from local cache! ⚡")
            
            # --- AUDIO FEATURES INIT ---
            st.info("Fetching Audio Features (Energy, Key, Mode) for Harmonic Mixing...")
            track_uris_for_audio = [item['track']['uri'] for item in tracks if item.get('track') and item['track'].get('uri') and not item['track']['uri'].startswith('spotify:local:')]
            audio_data_map = fetch_audio_features_with_cache(sp, track_uris_for_audio)
            
            import math
            current_date = datetime.now()
            
            seo_data = []
            for idx, item in enumerate(tracks):
                t = item.get('track')
                if t and t.get('uri') and not t['uri'].startswith('spotify:local:'):
                    
                    track_pop = t.get('popularity', 0)
                    artist_id = t['artists'][0]['id'] if t.get('artists') else None
                    artist_pop = artist_cache.get(artist_id, 50) if needs_advanced_metrics else 0
                    
                    # Calculate Age in Months
                    months_age = 0
                    if needs_advanced_metrics and t.get('album') and t['album'].get('release_date'):
                        rd = t['album']['release_date']
                        try:
                            # Handle different format "YYYY", "YYYY-MM", "YYYY-MM-DD"
                            if len(rd) == 4:
                                release_dt = datetime.strptime(rd, "%Y")
                            elif len(rd) == 7:
                                release_dt = datetime.strptime(rd, "%Y-%m")
                            else:
                                release_dt = datetime.strptime(rd, "%Y-%m-%d")
                            
                            delta = current_date - release_dt
                            months_age = max(0, delta.days // 30)
                        except Exception:
                            months_age = 12 # Default fake age on parse error
                            
                    # --- CALCULATE SCORES ---
                    score_native = track_pop
                    
                    capped_age = min(months_age, 60)
                    # Approach 1: Era Hybrid (Track 50, Artist 30, Age 20)
                    score_era = (track_pop * 0.5) + (artist_pop * 0.3) + (capped_age * 0.2)
                    
                    # Approach 3: Log Momentum
                    score_log = math.log10(track_pop + 1) * (1 + (artist_pop / 100)) + math.log(months_age + 1)
                    
                    # Determine final sorting score based on user choice
                    if "Native" in algo_choice:
                        final_score = score_native
                    elif "Era" in algo_choice:
                        final_score = round(score_era, 1)
                    else:
                        final_score = round(score_log, 2)
                        
                    # --- CURATOR OVERRIDE (BOOST MULTIPLIER) ---
                    is_favorite = t['uri'] in fav_uris
                    if is_favorite:
                        final_score = round(final_score * 1.4, 2)
                        
                    # --- AUDIO FEATURES MAPPING ---
                    t_uri = t['uri']
                    audio_ft = audio_data_map.get(t_uri, {"energy": 0.5, "key": 0, "mode": 1})
                    t_energy = audio_ft.get("energy", 0.5)
                    t_key = audio_ft.get("key", 0)
                    t_mode = audio_ft.get("mode", 1)
                    
                    # Map to Camelot Wheel String (e.g., '8A')
                    camelot_code = CAMELOT_DICT.get((t_key, t_mode), "Unknown")
                    
                    seo_data.append({
                        "Original #": idx + 1,
                        "Track Name": t.get('name', 'Unknown'),
                        "Artist": ", ".join(a.get('name', 'Unknown') for a in t.get('artists', [])),
                        "Algorithm Score 🏅": final_score,
                        "Energy ⚡": round(t_energy, 2),
                        "Camelot 🎵": camelot_code,
                        "Curator Boost 💖": "Yes (1.4x)" if is_favorite else "No",
                        "Native Track Pop": track_pop,
                        "Artist Pop": artist_pop if needs_advanced_metrics else "N/A",
                        "Months Old": months_age if needs_advanced_metrics else "N/A",
                        "Key": t_key,
                        "Mode": t_mode,
                        "URI": t_uri
                    })
            
            # --- GLOBAL MIN-MAX SCALING (0-100) ---
            if seo_data:
                raw_scores = [d["Algorithm Score 🏅"] for d in seo_data]
                min_score = min(raw_scores)
                max_score = max(raw_scores)
                
                for d in seo_data:
                    raw = d["Algorithm Score 🏅"]
                    if max_score > min_score:
                        d["Algorithm Score 🏅"] = round(((raw - min_score) / (max_score - min_score)) * 100, 1)
                    else:
                        d["Algorithm Score 🏅"] = 100.0
            
            st.session_state['seo_tracks'] = seo_data
            st.session_state['seo_playlist_id'] = selected_id
            st.session_state['seo_method'] = algo_choice
            st.success(f"Successfully analyzed {len(seo_data)} tracks using '{algo_choice.split('(')[0].strip()}'!")
            time.sleep(1)
            st.rerun()
            
    if st.session_state['seo_tracks']:
        st.info(f"Currently viewing analysis based on: **{st.session_state['seo_method']}**")
        st.divider()
        st.subheader("2. Playlist Sequencing & Optimizer")
        st.markdown("Select a strategy below to preview the expected playlist sequence. Once satisfied, execute the reorder.")
        
        seq_strategy = st.radio("Select Sequence Strategy:", [
            "Pin Top X Tracks Only",
            "The Rollercoaster (Energy Arcs)",
            "Hit Interleave (Anchor Discovery)",
            "Optimize for Flow (Anti-Clumping)",
            "🤖 Auto-Select Best Strategy"
        ])
        
        current_tracks = st.session_state['seo_tracks']
        
        if seq_strategy == "Pin Top X Tracks Only":
            top_x = st.slider("Select number of tracks to pin to the top:", min_value=5, max_value=50, value=20, step=1)
            # Preview Logic
            sorted_by_score = sorted(current_tracks, key=lambda x: x["Algorithm Score 🏅"], reverse=True)
            top_x_tracks = sorted_by_score[:top_x]
            top_x_uris = [t["URI"] for t in top_x_tracks]
            remaining = [t for t in current_tracks if t["URI"] not in top_x_uris]
            preview_tracks = top_x_tracks + remaining
        else:
            st.info("The algorithm will mathematically sequence the entire length of the playlist automatically.")
            top_x = 0
            # Preview Logic
            if "Rollercoaster" in seq_strategy:
                preview_tracks = apply_rollercoaster_wave_sort(current_tracks)
            elif "Interleave" in seq_strategy:
                preview_tracks = apply_hit_interleave_sort(current_tracks)
            elif "Flow" in seq_strategy:
                preview_tracks = apply_csp_flow_sort(current_tracks)
            else: # Auto
                preview_tracks, chosen = auto_select_sort(current_tracks)
                st.info(f"Auto-Select previewing via: {chosen}")
        
        df_preview = pd.DataFrame(preview_tracks)
        # We don't need to re-sort here, because preview_tracks is already in the final order
        # Re-inject viewing index
        df_preview.insert(0, "New Order #", range(1, 1 + len(df_preview)))
        
        st.dataframe(df_preview, use_container_width=True)
        
        
        if st.button("🚀 Push Sequence to Spotify (Execute Reorder)", type="primary"):
            with st.spinner("Reordering playlist..."):
                playlist_id = st.session_state['seo_playlist_id']
                # We already calculated the exact final list in `preview_tracks`
                optimized_uris = [t["URI"] for t in preview_tracks]
                if seq_strategy == "Pin Top X Tracks Only":
                    msg = f"Playlist optimized! Pinned top {top_x} tracks to the head."
                else:
                    msg = f"Playlist fully sequenced using '{seq_strategy}' algorithm!"
                
                # Execute replacement
                if not optimized_uris:
                    sp.playlist_replace_items(playlist_id, [])
                else:
                    sp.playlist_replace_items(playlist_id, optimized_uris[:100])
                    time.sleep(0.5)
                    
                    for chunk in chunk_list(optimized_uris[100:], 100):
                        sp.playlist_add_items(playlist_id, chunk)
                        time.sleep(0.5)
                        
                st.session_state['seo_tracks'] = []
                st.session_state['seo_playlist_id'] = None
                
                st.success(msg)
                time.sleep(2)
                st.rerun()
