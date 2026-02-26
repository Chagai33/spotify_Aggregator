import streamlit as st
import pandas as pd
import re
import time
import unicodedata
import spotipy
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import html
import json
from datetime import datetime

# Load environment variables (Client ID, Secret, Redirect URI)
load_dotenv()

# --- Configuration Definitions ---
TARGET_PLAYLISTS = {
    "Israeli Hip Hop": "1Ycl9i5uMtniDKs0jKvJOe",
    "Reggae": "3obWJRscGGN4QvmeLZK7US",
    "Israeli Music": "70y6Euzv1eUaYgR6Qzoo2r",
    "Country, Indie": "6QZz84AaYPlD1ALgrVacP4",
    "Melodic House": "7F8Bea5phhXrDwAx5rETPg",
    "Hip Hop, Rap": "3GiWLHwdkZU9VQ4i1aagWa",
    "Afrobeats": "1XyXp1FRHBRnvxmmhT5Sz6",
    "Mizrahi": "1zcEZURYYKMCvs4rpTB6ti",
    "Reggaeton": "09QZH7Nlj4vS9Paur6Srcm",
    "s3 למיין": "4qYupj1n5KASzFohe5RSmH"
}

GENRE_ROUTING_DICT = {
    "Israeli Hip Hop": ["Israeli Hip Hop", "Israeli Rap"],
    "Reggae": ["Reggae", "Modern Reggae", "Reggae Rock", "Indie Reggae", "West Coast Reggae"],
    "Israeli Music": ["Israeli Music", "Israeli Pop", "Israeli Indie", "Indie IL", "Israeli"],
    "Country, Indie": ["Country", "Country Pop", "Indie", "Indie Pop", "American Indie", "Indie Folk", "Pop, Folk", "Folk, Pop", "Indie Soul", "Soul Indie", "Retro soul", "Modern Indie Folk", "Modern Indie", "Indie Rock", "Alternative Indie", "Alternative Pop", "Acoustic Soul", "Folk Acoustic", "Folk-Soul", "Pop Soul", "Lo-Fi", "R And B", "R&B", "Rendb", "RB", "Soul", "Electro Chil", "Electro Chill", "Indie Modern Funk", "Acoustic Folk", "Folk", "Acoustic", "Pop", "Alternative Indie, Rock", "Meditation", "indie rock, pop"],
    "Melodic House": ["Melodic House", "Melodic Techno", "Tropical House", "Organic House", "Indie House", "Tech House", "Techno House", "Bass House", "Base House", "Funky Bass House", "Edm", "EDM House", "Electro House", "Funky House", "Fusion House", "Electropop", "Brazilian Edm", "Mix House", "Groove House", "House", "House Techno", "Techno", "Tech, Bass House", "Groove Metal", "bass / melodic house"],
    "Hip Hop, Rap": ["Hip Hop", "Rap", "Hip Hop, Rap", "Rap, Hip Hop", "UG Hip Hop", "Underground Hip Hop", "UG Hip Pop", "UG Rap", "Trap", "Dark Trap", "Latin Trap", "Bass Trap", "Hip Pop", "East Coast Hip Hop", "Multigenre Rap", "Dfw Rap", "London Rap", "Westcoast Rap", "West Coast Rap", "Drift Phonk", "Hip Hop Rap", "Hip Pop / Trap", "NYC"],
    "Afrobeats": ["Afrobeats", "Afrobeat", "Dancehall", "Kenyan Drill", "Dancehall Blend"],
    "Mizrahi": ["Mizrahi", "Mizrachi", "Yemeni Diwan"],
    "Reggaeton": ["Reggaeton", "Reggaton"],
    "s3 למיין": ["Mix", "Mix Gener", "Mixed Genres", "Spacial Intro"]
}

# --- Parallel Routing Configuration ---
RAW_ISRAELI_ARTISTS = [
    "2t", "ACCULBED", "Adam Ten (אדם טן)", "ASHER SWISSA (סקאזי)", "Asal (אסל)", "ATAR MAYNER (עטר מיינר)", "BĘÃTFÓØT (ביטפוט)", "BLNKY", "DE SOFFER (די סופר)", "E-Z (איזי)", "ECHO (אקו)", "EVILEAF", "Folly Tree (פולי טרי)", "Full Trunk (פול טראנק)", "Garden City Movement", "iogi (יוגב גלוסמן)", "iRO", "ILANZE", "Jacob (IL)", "JAMAA (ג'אמע)", "JETFIRE (ג'טפייר)", "JIGI", "Kiki Malinki (קיקי מלינקי)", "Kintsugi (קינצוגי)", "KLIN SADYLE (קלין סדייל)", "Koevary (קובארי)", "Lava Dome", "Mita Gami (מיטה גאמי)", "N-47", "OMRI. (עומרי.)", "PA'AM (פעם)", "REGINI", "ROMI (רומי)", "ROUSSO (רוסו)", "Saxtracks", "SHIRU (שירו)", "Soft Deep (סופט דיפ)", "Stargo (סטארגו)", "Sync (סינק)", "The White Screen (המסך הלבן)", "Vulkan (וולקן)", "YOYO (יויו)", "אבי אבורומי", "אביב בכר", "אביהו פנחסוב (מועדון הקצב של אביהו פנחסוב)", "אביחי נפתלי", "אביתר שמחי", "אבנר טואג", "אברהם איילאו", "אברהם לגסה", "אברי ג'י", "אגם בוחבוט", "אדמ", "אדיר גץ", "אודיה", "אודימן (Hoodyman)", "אופיר מלול", "אופק אדנק", "אופק נחמן", "אוראל (Orel)", "אורי סבאן", "אורי שוחט", "אורית טשומה", "אורטגה", "אורן ברזילי", "איזי (E-Z)", "איציק שמלי", "איתי גל (Itai Gal)", "איתי גלו (Itay Galo)", "איתי לוי", "איתמר יניב", "איתמר פיש", "אלדד ציטרין", "אלונה טל", "אלי חולי", "אליאור שמש", "אליעד", "אליעזר", "אלמאליכ (Almalik)", "אלמוג גוזלן", "אמיר בניון", "אמיר שדה", "אמסלם", "אנה זק", "אנדרדוג (Underdogg)", "אניס נקש", "אסקר (ASKER)", "ארז לב ארי", "אריאלה ברוך", "אשכנז (Ashken)", "אתל (Ethel)", "באלישג", "בום פם", "בוסקילז (Booskills)", "ביג ג'יי (Big-J)", "ביג סיזו (Big Sezo)", "בל דורון", "בן אל תבורי", "בן מירן", "בנאלי (Beneli)", "בר אלפנדרי", "בראדון (Bar Adon)", "ברי סחרוף", "בתאל סבח", "בתיאל סיסאי", "ג'יין בורדו", "ג'ני פנקין", "גיא מוזס", "גיא נוימן (Guy newman)", "גיא ויהל", "גיאגיא", "גל אדם", "גלדי (Galdi)", "גלעד כהנא", "גון בן ארי", "גורליק (Gorlik)", "גילי אסרף", "דוד ד'אור", "דוד לב ארי", "דוד מעיין", "דוד בן ארזה", "דודא", "דודו פארוק", "דון ג'וזף (Dawn Joseph.)", "דורון אזולאי", "דימה XR", "דינג'אן", "דן זיתון", "דניאל ברזילאי", "דניאל חן", "דניאל רובין", "דותן סיטבון", "הדר הלל", "היוצרים", "הילה פאר", "הילה רוח", "הצל", "התאומים (Twins DJ's)", "התקווה 6", "המשקפיים של נויפלד", "וולקן (Vulkan)", "ויוו (Vivo)", "וייזי (Vaizi)", "ויק אוחנה ז'אן", "זהבי (Zehavi)", "זיו", "זליג", "חיים אוליאל", "חיים משה", "חייאתי (Haya Avichar)", "חן פורתי", "חני מסלה", "חסן MC", "טהר", "טוכטי (Tochti)", "טונה", "טל כרמי", "טליסמאן", "טוקסיקו (Toxico)", "תום גפן", "תומר ורסצ'ה", "תומר יוסף", "תומר ישעיהו", "יא נה (Ya-Ne)", "יואב לפיד", "יוני בלוך", "יוני דויטש", "יונתן קלימי", "יוסי שטרית", "יושי", "יעל כהן", "יפעת בר סלע", "יפעת נטוביץ", "ירין פרימק", "ישי ריבו", "כהן", "כליפי (Kalifi)", "כפיר עזרן", "כרקוקלי", "לאה שבת", "לורן פלד", "ליאור נרקיס", "ליעד מאיר", "ליעם חכמון", "לירון עמרם", "ליר (LIR)", "לרוז (Laroz)", "מאי ויצמן", "מאי טוויק", "מאור אדרי", "מאור אלוש", "מאור אשכנזי", "מאיה בוסקילה", "מושיקו מור", "מור", "מורן מזור", "מיכאל רפאל", "מיכל זנדני", "מיקדו (Mikado)", "מיקה דוארי", "מיקה אלטמן!", "מיקי (Miki)", "מיש בז'רנו", "מירב הלינגר", "מיסטרמיס (Mistermiss)", "מק פיטוסי (Mc fitusi)", "נוגה ארז", "נוי פדלון", "נויה אוזן", "נוימן", "נועה קירל", "נועה שאואט", "נופר סלמאן", "נטורל (Natural)", "נינה קלור", "ניצן איזנברג", "נמש", "נרקיס", "נסרין קדרי", "נתלי", "סאבלימינל", "סבסטיאן XL", "סגול 59", "סול ספשיאל (Soul Special)", "סולטי (Salty)", "סידי (Sidi)", "סיוון", "סיון טלמור", "סימה נון", "סלים פים (Slimfim)", "ספיר סבן", "סטטיק", "סטפן לגר", "עברי לידר", "עדן בן זקן", "עדן דרסו", "עדן חסון", "עדן מאירי", "עומר אדם", "עומר מושקוביץ", "עומר נצר", "עומרי פילס", "עומרי 69 סגל", "עומרי סבח", "עידו בן דב", "עידו בי (Ido B)", "עידו מימון", "עידן חביב (עידן רפאל חביב)", "עידן צ'או", "עידן רייכל", "עילי בוטנר", "עלמה גוב", "עמיר בניון", "ענבל רז", "ענבר", "ערן יוסף", "ערן צור", "פאס (Fass)", "פטריק סבג", "פלד", "צגאי בוי", "צוקוש", "ציון ברוך", "ציון גולן", "צליל דנין", "צפריר", "קאפח", "קובי פרץ", "קורל ביסמוט", "קותימאן", "קרמזל (Karmazel)", "רביד פלוטניק", "רביב כנר", "רואי אדם", "רובי פאייר (Roby Fayer)", "רון בוחניק", "רון בי (Ron B)", "רון חיון", "רון כהן", "רון נשר", "רון פרץ", "רון פרטוק (ron.partuk)", "רונה קינן", "רוני דלומי", "רוני חבר", "רועי ריק", "רועי סנדלר", "רומן הולק", "רוי סופר (Royal Sopher)", "ריקו (Rico)", "ריף כהן", "רותם כהן", "רותם דורון", "רן דנקר", "שאזאמאט", "שגב", "שגיא דהן", "שחר יוסף", "שחר סאול", "שי בלנקו", "שי נחייסי", "שי (Shae)", "שילה אליה", "שירי מימון", "שירוטו (Shiroto)", "שיר גבאי", "שיר דוד גדסי", "שירה בן שמחון", "שירה זלוף", "שירה מלכה", "שירה מור", "שירת מפונים", "שירז אברהם", "שקל", "שלי ארצ'ר", "שלי פרל", "שריי אדר", "שרק (ShrekDiMC)", "שרית חדד", "ששון איפרם שאולוב", "תמר יהלומי", "תמר ריילי"
]

ISRAELI_ARTISTS_SET = set()
for entry in RAW_ISRAELI_ARTISTS:
    # Identify entries like "Adam Ten (אדם טן)"
    match = re.search(r"^(.*?)\s*\((.*?)\)$", entry)
    if match:
        ISRAELI_ARTISTS_SET.add(match.group(1).strip().lower())
        ISRAELI_ARTISTS_SET.add(match.group(2).strip().lower())
    else:
        ISRAELI_ARTISTS_SET.add(entry.strip().lower())

EXCLUSION_LIST = [g.lower() for g in ["Drum N Base", "Drum N Bass", "DrumNBase", "Uk Dnb", "UK DnB", "Dubstep", "Psytrance"]]

# Pre-process routing dictionary for O(1) case-insensitive lookup
REVERSE_ROUTING = {}
for target, genres in GENRE_ROUTING_DICT.items():
    for g in genres:
        REVERSE_ROUTING[g.lower()] = target

# --- API Helper Functions ---

@st.cache_data(show_spinner=False)
def parse_description(description):
    if not description:
        return []
        
    description = html.unescape(description)
    desc = unicodedata.normalize('NFKC', description)
    
    # BULLETPROOF CLEANING: Surgically remove the date prefix and "Created by" suffix
    # This strips everything up to and including 'Releases' (and an optional pipe)
    desc = re.sub(r'(?i)^.*?releases\s*\|?\s*', '', desc)
    # This strips 'Created by...' or 'Create by...' and an optional pipe
    desc = re.sub(r'(?i)\s*\|?\s*create[d]? by.*$', '', desc)
    
    genres_part = desc.strip()
    if not genres_part:
        return []

    parsed = []
    
    if '♩' in genres_part:
        segments = genres_part.split('♩')
        for seg in segments:
            seg = seg.strip(' .,')
            if not seg: continue
            
            m = re.search(r'^(.*?)\s*(\d+)?$', seg)
            if m:
                genre = m.group(1).strip(' .,/')
                count = m.group(2)
                # Strict Safeguard: If no count is specified, fail safely by skipping the playlist
                if not count: return None 
                parsed.append({"genre": genre, "count": int(count)})
    else:
        # No music note delimiter; split by digits
        has_numbers = bool(re.search(r'\d', genres_part))
        if has_numbers:
            matches = re.findall(r'([^\d]+)(\d+)', genres_part)
            for g, c in matches:
                parsed.append({"genre": g.strip(' .,/'), "count": int(c)})
        else:
            # Strict Safeguard: No numbers and no notes found
            return None 
                
    return parsed

def get_all_user_playlists(sp):
    """Fetches ALL user playlists with pagination to bypass 1000+ limits."""
    playlists = []
    offset = 0
    while True:
        results = sp.current_user_playlists(limit=50, offset=offset)
        if not results['items']:
            break
        playlists.extend(results['items'])
        if len(results['items']) < 50:
            break
        offset += len(results['items'])
    return playlists

def get_target_source_playlists(all_playlists):
    """Filters all playlists to find the 97 target source ones (Aum#201-297) and sorts them numerically."""
    pattern = re.compile(r'Aum#(20[1-9]|2[1-8][0-9]|29[0-7])')
    matched = []
    for p in all_playlists:
        if p and p.get('name') and pattern.search(p['name']):
            # Extract number for precise sorting
            num = int(pattern.search(p['name']).group(1))
            matched.append((num, p))
            
    # Sort by the extracted Aum# number
    matched.sort(key=lambda x: x[0])
    return [p for num, p in matched]

def get_all_playlist_tracks(sp, playlist_id):
    """Fetches ALL tracks from a playlist, handling pagination."""
    tracks = []
    offset = 0
    while True:
        results = sp.playlist_items(playlist_id, limit=100, offset=offset)
        if not results['items']:
            break
        tracks.extend(results['items'])
        if len(results['items']) < 100:
            break
        offset += len(results['items'])
    return tracks

def chunk_list(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def is_israeli_track(track_obj):
    """Determines if a track has Hebrew characters or an Israeli artist.
       Returns a tuple (is_israeli, is_fuzzy_match), where is_fuzzy_match 
       is True if matched only by English dictionary name."""
    if not track_obj:
        return False, False
        
    # Check track name for Hebrew characters
    track_name = track_obj.get('name', '')
    if re.search(r'[\u0590-\u05FF]', track_name):
        return True, False
        
    # Check artists
    artists = track_obj.get('artists', [])
    for artist in artists:
        artist_name = artist.get('name', '')
        if not artist_name:
            continue
            
        # Check artist name for Hebrew characters
        if re.search(r'[\u0590-\u05FF]', artist_name):
            return True, False
            
        # Check against parsed set 
        if artist_name.strip().lower() in ISRAELI_ARTISTS_SET:
            return True, True
            
    return False, False

# --- Streamlit UI & Logic ---

st.set_page_config(page_title="Spotify Playlist Aggregator", page_icon="🎧", layout="wide")

st.title("🎧 Spotify Seasonal Playlist Aggregator")
st.markdown("Automate the routing of tracks from your weekly playlists into 9 seasonal targets based on dynamic description parsing.")

# Authentication Setup via Streamlit Session State
if 'sp' not in st.session_state:
    try:
        scope = "playlist-read-private playlist-read-collaborative playlist-modify-public playlist-modify-private"
        sp_oauth = SpotifyOAuth(scope=scope, open_browser=False, cache_path=".spotifycachesl")
        
        # Check if we already have a token cached
        token_info = sp_oauth.get_cached_token()
        if not token_info:
            # Need to authenticate via URL in Streamlit
            auth_url = sp_oauth.get_authorize_url()
            st.warning("You must authenticate with Spotify first.")
            st.markdown(f"**[Click here to log in to Spotify]({auth_url})**")
            
            auth_code = st.text_input("Enter the Authorization URL you were redirected to:")
            if auth_code:
                try:
                    code = sp_oauth.parse_response_code(auth_code)
                    sp_oauth.get_access_token(code)
                    st.session_state['sp'] = spotipy.Spotify(auth_manager=sp_oauth)
                    st.success("Successfully authenticated!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Authentication failed: {e}")
            st.stop()
        else:
            st.session_state['sp'] = spotipy.Spotify(auth_manager=sp_oauth)
    except Exception as e:
        st.error(f"OAuth initialization failed. Make sure your .env variables are set. Details: {e}")
        st.stop()

sp = st.session_state['sp']

# Caching the heavy initial API calls so the UI doesn't lag on button clicks
@st.cache_data(show_spinner="Fetching 1000+ playlists from Spotify API...")
def load_source_playlists(_sp):
    all_pls = get_all_user_playlists(_sp)
    return get_target_source_playlists(all_pls)

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

# Sidebar status
st.sidebar.header("Status")
if st.sidebar.button("🔄 Refresh Data from Spotify"):
    st.cache_data.clear()
    st.rerun()
all_source_playlists = load_source_playlists(sp)
if not all_source_playlists:
    st.error("No source playlists matching `Aum#201-...` found.")
    st.stop()

st.sidebar.success(f"Loaded {len(all_source_playlists)} total Source Playlists.")

# Application State Configuration
st.session_state.setdefault("simulation_done", False)
st.session_state.setdefault("migration_done", False)
st.session_state.setdefault("current_playlist_index", 0)
st.session_state.setdefault("cumulative_audit_log", [])
st.session_state.setdefault("cleanup_uris", [])
st.session_state.setdefault("cleanup_overlap", [])
st.session_state.setdefault("cleanup_a_id", None)
st.session_state.setdefault("pending_preview", [])
st.session_state.setdefault("pending_staged", {})
st.session_state.setdefault("pending_batch_size", 0)
st.session_state.setdefault("pending_anomalies", set())

if 'target_existing_uris' not in st.session_state:
    st.session_state['target_existing_uris'] = load_target_existing_uris(sp)

tab1, tab2, tab3 = st.tabs(['🎧 Phase 1: Migration Engine', '🧹 Phase 2: Cross-Playlist Cleanup', '🛡️ Phase 3: Backup & Restore'])

with tab1:
    # 1. Visual Pre-Flight Check
    st.subheader("1. Identified Target Source Playlists")
    st.markdown("Playlists are correctly sorted chronologically by their `Aum#`.")
    with st.expander("View Source Playlists", expanded=False):
        df_sources = pd.DataFrame([{"Aum#": int(re.search(r'Aum#(20[1-9]|2[1-8][0-9]|29[0-7])', p['name']).group(1)), "Name": p['name'], "Tracks": p['tracks']['total'], "Description": p.get('description', '')} for p in all_source_playlists])
        st.dataframe(df_sources, use_container_width=True)
        
    # 2. Global Checksum Utility
    st.subheader("2. Global Checksum Utility")
    
    if "checksum_results" not in st.session_state:
        st.session_state["checksum_results"] = None
        
    def run_global_checksum(force_refresh_id=None):
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
        
    with st.expander("Run Validation on All Playlists", expanded=True):
        if st.button("🔍 Run Global Checksum"):
            with st.spinner("Validating all playlists..."):
                run_global_checksum()
                
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
                        run_global_checksum(force_refresh_id=r['ID'])
                        st.rerun()
            
            st.divider()
    
    def process_mapping(simulate_only=True, batch_size=2):
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
        
        start_idx = st.session_state["current_playlist_index"]
        end_idx = min(start_idx + batch_size, len(all_source_playlists))
        batch_playlists = all_source_playlists[start_idx:end_idx]
        
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
                        if target == "Hip Hop, Rap" and uri in local_existing_uris.get("Israeli Hip Hop", set()):
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
                    if target != "Israeli Music" and is_isr:
                        israeli_target = "Israeli Music"
                        
                        warning_flag = " ⚠️ Review" if is_fuzzy else ""

                        # Mutual Exclusion for Israeli Music
                        if target in ["Mizrahi", "Israeli Hip Hop"] or \
                           uri in local_existing_uris.get("Mizrahi", set()) or \
                           uri in local_existing_uris.get("Israeli Hip Hop", set()):
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
    
    # 3. Phase A: Batch Preview
    st.subheader("3. Phase A: Preview Batch Migration")
    
    remaining = len(all_source_playlists) - st.session_state['current_playlist_index']
    st.markdown(f"**Current Progress:** Processed `{st.session_state['current_playlist_index']}` out of `{len(all_source_playlists)}` playlists.")
    progress_val = st.session_state['current_playlist_index'] / len(all_source_playlists) if len(all_source_playlists) > 0 else 0
    st.progress(progress_val)
    
    if remaining > 0:
        c1, c2, c3, c4 = st.columns(4)
        batch_to_run = 0
        
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
                batch_log, staged_tracks, full_anomalies = process_mapping(simulate_only=True, batch_size=batch_to_run)
                
                # Store pending preview results in session state
                st.session_state['pending_preview'] = batch_log
                st.session_state['pending_staged'] = staged_tracks
                st.session_state['pending_anomalies'] = full_anomalies
                st.session_state['pending_batch_size'] = batch_to_run
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

    # If we have a pending preview staged, display the Dataframe and Execution buttons
    if st.session_state['pending_preview'] and st.session_state['pending_batch_size'] > 0:
        st.divider()
        st.subheader("Preview (Action Required)")
        sim_df = pd.DataFrame(st.session_state['pending_preview'])
        st.dataframe(sim_df, use_container_width=True)
        
        if st.session_state['pending_anomalies']:
            st.warning(f"Unmapped Genres Detected: {', '.join(st.session_state['pending_anomalies'])}")
            
        st.subheader("4. Phase B: Execute Batch")
        
        col_ok, col_cancel = st.columns([1, 4])
        
        with col_ok:
            if st.button("✅ Confirm & Push to Spotify", type="primary"):
                staged_tracks = st.session_state['pending_staged']
                batch_run = st.session_state['pending_batch_size']
                
                with st.status(f"Uploading Batch ({batch_run} playlists)...", expanded=True) as status:
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
                    status.update(label="Batch Upload Complete!", state="complete", expanded=False)
                
                # Update cumulative State
                start_num = st.session_state["current_playlist_index"]
                st.session_state["current_playlist_index"] += batch_run
                st.session_state["cumulative_audit_log"].extend(st.session_state['pending_preview'])
                
                # Update local URIs so the next batch knows about the tracks we just appended
                for tgt, uris in staged_tracks.items():
                    st.session_state['target_existing_uris'][tgt].update(uris)
                    
                # Clear pending states safely
                st.session_state['pending_preview'] = []
                st.session_state['pending_staged'] = {}
                st.session_state['pending_batch_size'] = 0
                st.session_state['pending_anomalies'] = set()
                
                st.success(f"Successfully processed playlists index {start_num} through {start_num + batch_run - 1}!")
                time.sleep(1.5)
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

with tab2:
    st.header("🧹 Cross-Playlist Cleanup Utility")
    st.markdown("Safely remove tracks from **Playlist A** that already exist in **Playlist B**.")
    
    # Fetch all user playlists to populate dropdowns
    all_user_playlists = get_all_user_playlists(sp)
    playlist_options = {p['name']: p['id'] for p in all_user_playlists}
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Playlist to Clean (Target A)")
        st.caption("Tracks will be deleted FROM this playlist.")
        a_dropdown = st.selectbox("Select Playlist A", options=list(playlist_options.keys()), key="cleanup_a_sel")
        a_url = st.text_input("Or enter Spotify URL for Playlist A", key="cleanup_a_url", placeholder="https://open.spotify.com/playlist/...")
        
    with col2:
        st.subheader("Reference Playlist (Target B)")
        st.caption("Tracks found HERE will be deleted from Target A.")
        b_dropdown = st.selectbox("Select Playlist B", options=list(playlist_options.keys()), key="cleanup_b_sel")
        b_url = st.text_input("Or enter Spotify URL for Playlist B", key="cleanup_b_url", placeholder="https://open.spotify.com/playlist/...")
        
    def extract_playlist_id(input_str):
        if not input_str: return None
        # Extract ID from standard Spotify URL or URI
        match = re.search(r'playlist[:/]([a-zA-Z0-9]+)', input_str)
        return match.group(1) if match else input_str.strip()

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
                
    if st.session_state.get('cleanup_uris'):
        st.divider()
        st.warning(f"Found {len(st.session_state['cleanup_uris'])} overlapping tracks ready for deletion.")
        st.dataframe(pd.DataFrame(st.session_state['cleanup_overlap']), use_container_width=True)
        
        col_exec1, col_exec2 = st.columns([1, 4])
        
        with col_exec1:
            if st.button(f"🗑️ Delete {len(st.session_state['cleanup_uris'])} Tracks", type="primary"):
                with st.spinner("Deleting tracks from Playlist A..."):
                    uris = st.session_state['cleanup_uris']
                    playlist_id_to_clean = st.session_state['cleanup_a_id']
                    
                    # Delete in chunks of 100
                    for chunk in chunk_list(uris, 100):
                        sp.playlist_remove_all_occurrences_of_items(playlist_id_to_clean, chunk)
                        time.sleep(0.5)
                        
                st.success("Successfully deleted overlapping tracks!")
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

with tab3:
    st.header("🛡️ Phase 3: Backup & Restore")
    st.markdown("Create snapshots of your target playlists before migrations, and restore them if necessary.")
    
    st.subheader("📦 Part 1: Create Snapshot (Backup)")
    if st.button("Create Target Playlists Snapshot", type="primary"):
        with st.spinner("Fetching current tracks from all target playlists..."):
            backup_data = {}
            for name, p_id in TARGET_PLAYLISTS.items():
                tracks = get_all_playlist_tracks(sp, p_id)
                # Keep only valid URIs
                uris = [item['track']['uri'] for item in tracks if item.get('track') and item['track'].get('uri') and not item['track']['uri'].startswith('spotify:local:')]
                backup_data[name] = uris
            
            json_str = json.dumps(backup_data, indent=2)
            date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"spotify_backup_{date_str}.json"
            
            st.success("Snapshot created successfully!")
            st.download_button(
                label=f"⬇️ Download {filename}",
                data=json_str,
                file_name=filename,
                mime="application/json"
            )
            
    st.divider()
    st.subheader("⚠️ Part 2: Restore from Snapshot (Rollback)")
    uploaded_file = st.file_uploader("Upload a backup JSON file", type=["json"])
    
    if uploaded_file is not None:
        try:
            restore_data = json.load(uploaded_file)
            st.write("Backup Contents:")
            
            # Display summary
            summary = [{"Playlist": k, "Tracks": len(v)} for k, v in restore_data.items()]
            st.dataframe(pd.DataFrame(summary), use_container_width=True)
            
            if st.button("⚠️ DANGER: Restore from Backup (Overwrite Current State)", type="primary"):
                with st.spinner("Restoring playlists..."):
                    for name, uris in restore_data.items():
                        if name not in TARGET_PLAYLISTS:
                            continue
                            
                        target_id = TARGET_PLAYLISTS[name]
                        st.write(f"Restoring `{name}` ({len(uris)} tracks)...")
                        
                        if not uris:
                            sp.playlist_replace_items(target_id, [])
                        else:
                            # Replace first 100 to clear existing and set first chunk
                            sp.playlist_replace_items(target_id, uris[:100])
                            time.sleep(0.5)
                            
                            # Add remaining tracks in chunks of 100
                            for chunk in chunk_list(uris[100:], 100):
                                sp.playlist_add_items(target_id, chunk)
                                time.sleep(0.5)
                                
                    # Reset session state caches to reflect restored state
                    st.session_state['target_existing_uris'] = load_target_existing_uris(sp)
                    st.success("Restore complete! All target playlists have been reverted to the backup state.")
                    time.sleep(2)
                    st.rerun()
                    
        except json.JSONDecodeError:
            st.error("Invalid JSON file uploaded.")
