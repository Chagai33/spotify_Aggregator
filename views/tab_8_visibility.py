import streamlit as st
import pandas as pd
import re
import time
import datetime
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
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

def get_stranger_view_playlist_ids(user_id):
    """Fetches playlists visible to an anonymous guest using Client Credentials."""
    try:
        from config.settings import SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET
        # Instantiate an anonymous client
        cc_manager = SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET)
        sp_stranger = spotipy.Spotify(client_credentials_manager=cc_manager)
        
        public_playlists = []
        results = sp_stranger.user_playlists(user_id)
        public_playlists.extend(results['items'])
        
        while results['next']:
            results = sp_stranger.next(results)
            public_playlists.extend(results['items'])
            
        return set(p['id'] for p in public_playlists if p is not None)
    except Exception as e:
        print(f"Error fetching stranger view: {e}")
        return set()

def render_tab8(sp):
    st.header("Phase 8: Profile Visibility Manager")
    st.markdown("Easily control which playlists appear publicly on your Spotify profile.")
    
    # --- 1. Load Data & Refresh Button ---
    col1, col2 = st.columns([4, 1])
    
    if col2.button("🔄 Refresh Data from Spotify", use_container_width=True):
        # Force refresh by removing the cached key if it exists
        if 'visibility_data' in st.session_state:
            del st.session_state['visibility_data']
            
    if 'visibility_last_updated' in st.session_state:
        col1.markdown(f"*Last updated directly from Spotify: **{st.session_state['visibility_last_updated']}** (Local Time)*")
        
    if 'visibility_data' not in st.session_state:
        with st.spinner("Fetching visibility data from Spotify..."):
            try:
                all_playlists = get_all_user_playlists(sp)
                my_user_id = sp.me()['id']
                
                # Fetch Stranger View
                stranger_visible_ids = get_stranger_view_playlist_ids(my_user_id)
                
                # Rebuild our structured data
                visibility_data = []
                for p in all_playlists:
                    # Need to check if user owns it to safely toggle it later
                    is_owner = p['owner']['id'] == my_user_id 
                    is_stranger_visible = p['id'] in stranger_visible_ids
                    
                    visibility_data.append({
                        "ID": p['id'],
                        "Name": p['name'],
                        "Series": get_series_name(p['name']),
                        "API Public Flag": p.get('public', False),
                        "Stranger View": is_stranger_visible,
                        "Planned Public": p.get('public', False), # Default: no change
                        "Tracks": p['tracks']['total'],
                        "Is Owner": is_owner
                    })
                    
                st.session_state['visibility_data'] = visibility_data
                st.session_state['visibility_last_updated'] = time.strftime("%Y-%m-%d %H:%M:%S")
                st.success("Successfully loaded your playlists.")
                st.rerun() # Refresh to show timestamp immediately
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
    
    col1, col2, col3 = st.columns([2, 1.5, 1.5])
    selected_series = col1.selectbox("Filter by Series / Group:", ["All Playlists"] + series_options)
    
    visibility_filter = col2.selectbox(
        "Visibility Filter:", 
        ["All", "Public (Stranger View)", "Private (Stranger View)", "Public (API Flag)", "Private (API Flag)"]
    )
    
    search_term = col3.text_input("Or Search by Name:", "")
    
    # Filter the working set for display/actions
    filtered_view = v_data
    
    if selected_series != "All Playlists":
        filtered_view = [item for item in filtered_view if item['Series'] == selected_series]
        
    if visibility_filter == "Public (Stranger View)":
        filtered_view = [item for item in filtered_view if item['Stranger View']]
    elif visibility_filter == "Private (Stranger View)":
        filtered_view = [item for item in filtered_view if not item['Stranger View']]
    elif visibility_filter == "Public (API Flag)":
        filtered_view = [item for item in filtered_view if item['API Public Flag']]
    elif visibility_filter == "Private (API Flag)":
        filtered_view = [item for item in filtered_view if not item['API Public Flag']]
        
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
        cols = st.columns([1, 4, 1.5, 1, 1.5, 2, 2, 2])
        
        # Indicator of change
        if item["Planned Public"] != item["API Public Flag"]:
            cols[0].write("⚠️ Changed")
        else:
            cols[0].write("-")
            
        cols[1].write(f"**{item['Name']}**")
        cols[2].write(f"`{item['Series']}`")
        cols[3].write(f"🎵 {item['Tracks']}")
        
        # Manual fetch button & Details Display
        details_key = f"details_{item['ID']}"
        if "Followers" in item:
            cols[4].caption(f"👥 {item.get('Followers', 'N/A')}\n📅 {item.get('Last Updated', 'N/A')}")
        else:
            if cols[4].button("📥 Details", key=f"btn_{item['ID']}", help="Fetch Followers & Last Updated"):
                with st.spinner("Fetching..."):
                    try:
                        # Fetch precise data for this one playlist
                        pl_data = sp.playlist(item['ID'], fields="followers,tracks.items(added_at)")
                        followers = pl_data['followers']['total']
                        
                        # Find the most recent 'added_at' date
                        last_updated = "Unknown"
                        if pl_data['tracks']['items']:
                            dates = [t['added_at'] for t in pl_data['tracks']['items'] if t and t.get('added_at')]
                            if dates:
                                latest_iso = max(dates)
                                # Parse and format: 2023-10-24T00:00:00Z -> 2023-10-24
                                if latest_iso:
                                    last_updated = latest_iso.split('T')[0]
                                
                        item["Followers"] = followers
                        item["Last Updated"] = last_updated
                        st.rerun()
                    except Exception as e:
                        st.error("Failed to fetch")
        
        # Stranger View indicator (the real truth)
        if item["Stranger View"]:
            cols[5].success("Visible 👁️")
        else:
            cols[5].error("Hidden 🔒")
        
        # API Flag indicator
        cols[6].caption(f"API Flag:\n{'Public 👁️' if item['API Public Flag'] else 'Private 🔒'}")
        
        # Toggle boolean for the 'Planned Public'
        toggle_key = f"toggle_{item['ID']}"
        if toggle_key in st.session_state:
            item["Planned Public"] = st.session_state[toggle_key]
            
        new_planned = cols[7].checkbox(
            "Set Public", 
            value=item["Planned Public"], 
            key=toggle_key,
            disabled=not item["Is Owner"]
        )
        
        if new_planned != item["Planned Public"]:
            item["Planned Public"] = new_planned

    # --- 3. Preview Pipeline (Dry Run) ---
    st.divider()
    st.subheader("2. Review & Commit")
    
    # Calculate Delta (what actually changed from Current to Planned)
    changes_to_make = [item for item in v_data if item["API Public Flag"] != item["Planned Public"]]
    
    if not changes_to_make:
        st.info("No visibility changes pending. Use the toggles above to configure changes.")
    else:
        st.warning(f"You have **{len(changes_to_make)}** playlists pending a visibility change.")
        
        delta_df = pd.DataFrame([{
            "Playlist": c["Name"],
            "Series": c["Series"],
            "From": 'Public 👁️' if c["API Public Flag"] else 'Private 🔒',
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
                        item["API Public Flag"] = item["Planned Public"]
                        successes += 1
                        
                        # Throttle to prevent rate limits
                        time.sleep(0.4) 
                        
                    except Exception as e:
                        st.error(f"Failed to update '{item['Name']}': {str(e)}")
                        errors += 1
                        
                status.update(label="Commit Complete!", state="complete")
                
            st.success(f"Successfully updated {successes} playlists. Encountered {errors} errors.")
            st.button("Close and Refresh")
