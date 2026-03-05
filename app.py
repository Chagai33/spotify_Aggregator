import streamlit as st

# 1. Configuration & Secrets Loading
import config.settings

# 2. Core Initializations
from core.state_manager import init_session_state
from core.auth import enforce_authentication
from core.spotify_client import get_all_user_playlists

# 3. Import Views
from views.tab_1_migration import render_tab1
from views.tab_2_cleanup import render_tab2
from views.tab_3_backup import render_tab3
from views.tab_4_insights import render_tab4
from views.tab_5_seo import render_tab5
from views.tab_6_rename import render_tab6
from views.tab_7_orphans import render_tab7

# --- PAGE CONFIG ---
st.set_page_config(page_title="Spotify Curator Tool", page_icon="🎵", layout="wide")

st.title("🎵 Comprehensive Curator Aggregator (Phase 1-7)")

# --- INITIALIZE SESSION STATE ---
init_session_state()

# --- AUTHENTICATION ---
sp_client = enforce_authentication()

if not sp_client:
    st.info("Please log in to Spotify to continue.")
    st.stop()
else:
    # --- LOAD GLOBAL DATA (IF NEEDED ACROSS TABS) ---
    if not st.session_state.get('global_playlists'):
        with st.spinner("Fetching all playlists..."):
            st.session_state['global_playlists'] = get_all_user_playlists(sp_client)

    # --- RENDER TABS ---
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "Phase 1: Migration Engine",
        "Phase 2: Cleanup",
        "Phase 3: Backup",
        "Phase 4: Insights",
        "Phase 5: SEO & Sequencer",
        "Phase 6: Rename",
        "Phase 7: Orphans"
    ])

    from core.spotify_client import get_target_source_playlists
    with tab1:
        source_playlists = get_target_source_playlists(st.session_state['global_playlists'])
        render_tab1(sp_client, source_playlists)
    
    with tab2:
        render_tab2(sp_client)
        
    with tab3:
        render_tab3(sp_client)
        
    with tab4:
        render_tab4(sp_client)
        
    with tab5:
        render_tab5(sp_client)
        
    with tab6:
        render_tab6(sp_client)
        
    with tab7:
        render_tab7(sp_client)
