import re
import time
import pandas as pd
import streamlit as st
from core.spotify_client import get_all_user_playlists

def render_tab6(sp):
    st.header("🏷️ Phase 6: Rename Seasonal Playlists")
    st.markdown("Safely rename playlists from `Aum#` to `Week#` specifically for season `200-300`.")
    
    if "rename_matches" not in st.session_state:
        st.session_state["rename_matches"] = []
    if "rename_index" not in st.session_state:
        st.session_state["rename_index"] = 0
        
    if st.button("🔍 Scan for Playlists (Week#200-300)", type="primary"):
        with st.spinner("Scanning all playlists..."):
            all_pls = get_all_user_playlists(sp)
            # Find playlists with Week#200 to Week#300
            pattern = re.compile(r'Week#(2[0-9]{2}|300)')
            matches = []
            for p in all_pls:
                if p and p.get('name'):
                    name = p['name']
                    if pattern.search(name):
                        # The user already renamed them, so for now we just list them or prepare for next step
                        # We'll just set New Name to be the same so the table doesn't break
                        new_name = name 

                        matches.append({
                            "ID": p['id'],
                            "Old Name": name,
                            "New Name": new_name
                        })
            
            if matches:
                # sort by the number in the aum#
                matches.sort(key=lambda x: int(pattern.search(x['Old Name']).group(1)))
                st.session_state["rename_matches"] = matches
                st.session_state["rename_index"] = 0
                st.success(f"Found {len(matches)} playlists matching criteria!")
                time.sleep(1)
            else:
                st.session_state["rename_matches"] = []
                st.session_state["rename_index"] = 0
                st.warning("No matches found in your account.")
            st.rerun()

    matches = st.session_state.get("rename_matches", [])
    idx = st.session_state.get("rename_index", 0)

    if matches:
        st.divider()
        st.markdown(f"**Total identified:** `{len(matches)}` | **Completed:** `{idx}`")
        progress_val = min(1.0, idx / len(matches))
        st.progress(progress_val)
        
        if idx < len(matches):
            batch = matches[idx:idx+5]
            st.subheader(f"Current Batch (Playlists {idx+1} to {idx+len(batch)})")
            
            # Display preview table
            df_batch = pd.DataFrame(batch).drop(columns=["ID"])
            st.dataframe(df_batch, use_container_width=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("✅ Approve & Rename Batch on Spotify", type="primary"):
                    with st.spinner("Renaming batch..."):
                        for item in batch:
                            sp.playlist_change_details(item['ID'], name=item['New Name'])
                            time.sleep(0.15)
                        st.session_state["rename_index"] += len(batch)
                        st.success("Batch renamed successfully!")
                        # Clear cache locally, avoiding modifying other modules
                        st.session_state.pop("global_playlists", None)
                        time.sleep(1)
                        st.rerun()
            with col2:
                if st.button("⏭️ Skip Batch"):
                    st.session_state["rename_index"] += len(batch)
                    st.rerun()
                    
            with col3:
                if st.button("❌ Cancel / Reset", type="secondary"):
                    st.session_state["rename_matches"] = []
                    st.session_state["rename_index"] = 0
                    st.rerun()
                
        else:
            st.success("🎉 All batches processed!")
            if st.button("🔄 Reset"):
                st.session_state["rename_matches"] = []
                st.session_state["rename_index"] = 0
                st.rerun()
