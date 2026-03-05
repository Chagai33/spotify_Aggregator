import streamlit as st
import pandas as pd
import re
import time
from core.spotify_client import get_all_user_playlists

def get_series_name(playlist_name):
    """Categorizes a playlist name into its respective series."""
    name_lower = playlist_name.lower()
    
    if re.search(r'^week#\d+', name_lower):
        return "Week# Series"
    elif re.search(r'^aum#\d+', name_lower):
        return "Aum# Series"
    elif "outofplaylist" in name_lower:
        return "Outofplaylist Series"
    else:
        return "Mainstream / Stand-alone"

def render_tab8(sp):
    st.header("Phase 8: Profile Visibility Manager")
    st.markdown("Easily control which playlists appear publicly on your Spotify profile.")
    
    # --- 1. Load Data ---
    if 'visibility_data' not in st.session_state or st.button("🔄 Refresh Data from Spotify"):
        with st.spinner("Fetching visibility data from Spotify..."):
            try:
                all_playlists = get_all_user_playlists(sp)
                my_user_id = sp.me()['id']
                
                # Rebuild our structured data
                visibility_data = []
                for p in all_playlists:
                    # Need to check if user owns it to safely toggle it later
                    is_owner = p['owner']['id'] == my_user_id 
                    
                    visibility_data.append({
                        "ID": p['id'],
                        "Name": p['name'],
                        "Series": get_series_name(p['name']),
                        "Current Public": p.get('public', False),
                        "Planned Public": p.get('public', False), # Default: no change
                        "Tracks": p['tracks']['total'],
                        "Is Owner": is_owner
                    })
                    
                st.session_state['visibility_data'] = visibility_data
                st.success("Successfully loaded your playlists.")
            except Exception as e:
                import spotipy
                if isinstance(e, spotipy.exceptions.SpotifyException) and e.http_status == 429:
                    st.error("⚠️ **Spotify API Rate Limit Reached (429 Too Many Requests)**.\nYou have made too many requests recently. Please wait a few minutes before trying again.")
                else:
                    st.error(f"❌ **Failed to fetch playlists from Spotify:**\n{str(e)}")
                st.stop()
            
    if not st.session_state.get('visibility_data'):
        st.stop()
        
    v_data = st.session_state['visibility_data']
    
    # --- 2. Action Controls ---
    st.subheader("1. Configure Visibility Actions")
    
    # Identify unique series
    series_options = sorted(list(set(item['Series'] for item in v_data)))
    
    col1, col2 = st.columns(2)
    selected_series = col1.selectbox("Filter by Series / Group:", ["All Playlists"] + series_options)
    
    # Filter the working set for display/actions
    if selected_series == "All Playlists":
        filtered_view = v_data
    else:
        filtered_view = [item for item in v_data if item['Series'] == selected_series]
        
    search_term = col2.text_input("Or Search by Name (optional):", "")
    if search_term:
        filtered_view = [item for item in filtered_view if search_term.lower() in item['Name'].lower()]
        
    st.markdown("---")
    st.write(f"**Showing {len(filtered_view)} Playlists**")
    
    # Bulk actions on the currently filtered view
    c1, c2 = st.columns(2)
    if c1.button("👁️ Mark All Displayed as PUBLIC"):
        for item in filtered_view:
            item["Planned Public"] = True
            st.session_state[f"toggle_{item['ID']}"] = True
        st.rerun()
            
    if c2.button("🔒 Mark All Displayed as PRIVATE"):
        for item in filtered_view:
            item["Planned Public"] = False
            st.session_state[f"toggle_{item['ID']}"] = False
        st.rerun()

    # Fine-grained Table with individual toggles
    st.markdown("*(You can also override individual playlists below:)*")
    
    # We display a custom table using columns to allow toggles next to rows
    for item in filtered_view:
        cols = st.columns([1, 4, 2, 2, 2])
        
        # Indicator of change
        if item["Planned Public"] != item["Current Public"]:
            cols[0].write("⚠️ Changed")
        else:
            cols[0].write("-")
            
        cols[1].write(f"**{item['Name']}**")
        cols[2].write(f"`{item['Series']}`")
        cols[3].caption(f"Current: {'Public 👁️' if item['Current Public'] else 'Private 🔒'}")
        
        # Toggle boolean for the 'Planned Public'
        # Check if Streamlit holds a new value in session state for this toggle
        toggle_key = f"toggle_{item['ID']}"
        if toggle_key in st.session_state:
            item["Planned Public"] = st.session_state[toggle_key]
            
        new_planned = cols[4].checkbox(
            "Set Public", 
            value=item["Planned Public"], 
            key=toggle_key,
            disabled=not item["Is Owner"]
        )
        
        # We NO LONGER call st.rerun() here. 
        # The key binding automatically updates session state and triggers a rerun by itself when the user clicks it.
        if new_planned != item["Planned Public"]:
            item["Planned Public"] = new_planned

    # --- 3. Preview Pipeline (Dry Run) ---
    st.divider()
    st.subheader("2. Review & Commit")
    
    # Calculate Delta (what actually changed from Current to Planned)
    changes_to_make = [item for item in v_data if item["Current Public"] != item["Planned Public"]]
    
    if not changes_to_make:
        st.info("No visibility changes pending. Use the toggles above to configure changes.")
    else:
        st.warning(f"You have **{len(changes_to_make)}** playlists pending a visibility change.")
        
        delta_df = pd.DataFrame([{
            "Playlist": c["Name"],
            "Series": c["Series"],
            "From": 'Public 👁️' if c["Current Public"] else 'Private 🔒',
            "To": 'Public 👁️' if c["Planned Public"] else 'Private 🔒'
        } for c in changes_to_make])
        
        st.dataframe(delta_df, use_container_width=True)
        
        # --- 4. Execution ---
        if st.button("🔥 COMMIT CHANGES TO SPOTIFY 🔥", type="primary"):
            with st.status("Executing changes safely...", expanded=True) as status:
                successes = 0
                errors = 0
                
                for idx, item in enumerate(changes_to_make):
                    try:
                        st.write(f"Updating '{item['Name']}' -> {'Public' if item['Planned Public'] else 'Private'} [{idx+1}/{len(changes_to_make)}]...")
                        
                        # API Call
                        sp.playlist_change_details(item['ID'], public=item['Planned Public'])
                        
                        # Update the local state so it reflects reality
                        item["Current Public"] = item["Planned Public"]
                        successes += 1
                        
                        # Throttle to prevent rate limits
                        time.sleep(0.4) 
                        
                    except Exception as e:
                        st.error(f"Failed to update '{item['Name']}': {str(e)}")
                        errors += 1
                        
                status.update(label="Commit Complete!", state="complete")
                
            st.success(f"Successfully updated {successes} playlists. Encountered {errors} errors.")
            st.button("Close and Refresh")
