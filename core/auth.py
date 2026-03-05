import spotipy
from spotipy.oauth2 import SpotifyOAuth
import streamlit as st

def enforce_authentication():
    """
    Checks if 'sp' is in session_state. If not, runs the auth flow UI.
    Calls st.stop() if not authenticated, halting the rest of the app execution.
    Returns the authenticated spotipy object.
    """
    if 'sp' not in st.session_state or st.session_state['sp'] is None:
        try:
            scope = "playlist-read-private playlist-read-collaborative playlist-modify-public playlist-modify-private"
            sp_oauth = SpotifyOAuth(scope=scope, open_browser=False, cache_path=".spotifycachesl")
            
            token_info = sp_oauth.get_cached_token()
            if not token_info:
                auth_url = sp_oauth.get_authorize_url()
                st.warning("Please authorize the app by clicking the link below:")
                st.markdown(f'<a href="{auth_url}" target="_self">Log in to Spotify</a>', unsafe_allow_html=True)
                
                auth_code = st.text_input("Enter the URL you were redirected to:")
                if auth_code:
                    try:
                        code = sp_oauth.parse_response_code(auth_code)
                        sp_oauth.get_access_token(code)
                        st.session_state['sp'] = spotipy.Spotify(auth_manager=sp_oauth, requests_timeout=5, status_retries=0)
                        st.success("Successfully authenticated!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Authentication failed: {e}")
                st.stop()
            else:
                st.session_state['sp'] = spotipy.Spotify(auth_manager=sp_oauth, requests_timeout=5, status_retries=0)
        except Exception as e:
            st.error(f"OAuth initialization failed. Make sure your .env variables are set. Details: {e}")
            st.stop()
            
    return st.session_state['sp']
