import streamlit as st

def init_session_state():
    """Initializes all necessary session state variables to prevent KeyErrors across tabs."""
    # Auth
    if 'sp' not in st.session_state:
        st.session_state['sp'] = None
    
    # Global Data
    if 'global_playlists' not in st.session_state:
        st.session_state['global_playlists'] = []
    if 'all_playlists_stats' not in st.session_state:
        st.session_state['all_playlists_stats'] = {}
        
    # Phase 1 Migration
    if 'current_playlist_index' not in st.session_state:
        st.session_state['current_playlist_index'] = 0
    if 'target_existing_uris' not in st.session_state:
        st.session_state['target_existing_uris'] = {}
    if 'cumulative_audit_log' not in st.session_state:
        st.session_state['cumulative_audit_log'] = []
    if 'pending_preview' not in st.session_state:
        st.session_state['pending_preview'] = []
    if 'pending_staged' not in st.session_state:
        st.session_state['pending_staged'] = {}
    if 'pending_batch_size' not in st.session_state:
        st.session_state['pending_batch_size'] = 0
    if 'pending_mode' not in st.session_state:
        st.session_state['pending_mode'] = 'batch'
    if 'pending_anomalies' not in st.session_state:
        st.session_state['pending_anomalies'] = set()
        
    # Phase 2 Cleanup
    if 'cleanup_uris' not in st.session_state:
        st.session_state['cleanup_uris'] = []
    if 'cleanup_overlap' not in st.session_state:
        st.session_state['cleanup_overlap'] = []
    if 'cleanup_a_id' not in st.session_state:
        st.session_state['cleanup_a_id'] = None
        
    # Phase 5 SEO
    if 'seo_tracks' not in st.session_state:
        st.session_state['seo_tracks'] = []
    if 'seo_playlist_id' not in st.session_state:
        st.session_state['seo_playlist_id'] = None
    if 'seo_method' not in st.session_state:
        st.session_state['seo_method'] = "1. Spotify Native (Track Popularity Only)"
        
    # Phase 6 Rename
    if 'rename_matches' not in st.session_state:
        st.session_state['rename_matches'] = []
    if 'rename_index' not in st.session_state:
        st.session_state['rename_index'] = 0
        
    # Phase 7 Orphans
    if 'p7_orphans' not in st.session_state:
        st.session_state['p7_orphans'] = []
    if 'p7_master_id' not in st.session_state:
        st.session_state['p7_master_id'] = None
    if 'p7_dest_id' not in st.session_state:
        st.session_state['p7_dest_id'] = None
