import streamlit as st
import pandas as pd
import re
import time
import unicodedata
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

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
    "Reggaeton": "09QZH7Nlj4vS9Paur6Srcm"
}

GENRE_ROUTING_DICT = {
    "Israeli Hip Hop": ["Israeli Hip Hop", "Israeli Rap"],
    "Reggae": ["Reggae", "Modern Reggae", "Reggae Rock", "Indie Reggae", "West Coast Reggae"],
    "Israeli Music": ["Israeli Music", "Israeli Pop", "Israeli Indie", "Indie IL"],
    "Country, Indie": ["Country", "Country Pop", "Indie", "Indie Pop", "American Indie", "Indie Folk", "Pop, Folk", "Folk, Pop", "Indie Soul", "Soul Indie", "Retro soul", "Modern Indie Folk", "Modern Indie", "Indie Rock", "Alternative Indie", "Alternative Pop", "Acoustic Soul", "Folk Acoustic", "Folk-Soul", "Pop Soul", "Lo-Fi", "R And B", "Rendb", "RB", "Meditation", "Chill Indie", "Spacial Intro", "Electro Chil", "Indie Modern Funk"],
    "Melodic House": ["Melodic House", "Melodic Techno", "Tropical House", "Organic House", "Indie House", "Tech House", "Techno House", "Bass House", "Base House", "Funky Bass House", "Edm", "EDM House", "Electro House", "Funky House", "Fusion House", "Electropop", "Brazilian Edm", "Mix House", "Groove House", "House", "Mix Gener", "Mix", "Groove Metal"],
    "Hip Hop, Rap": ["Hip Hop", "Rap", "Hip Hop, Rap", "Rap, Hip Hop", "UG Hip Hop", "Underground Hip Hop", "UG Hip Pop", "Trap", "Dark Trap", "Latin Trap", "Bass Trap", "Hip Pop", "East Coast Hip Hop", "Multigenre Rap", "Dfw Rap", "London Rap", "Westcoast Rap", "West Coast Rap", "Drift Phonk", "Hip Hop Rap", "Hip Pop / Trap"],
    "Afrobeats": ["Afrobeats", "Afrobeat", "Dancehall", "Kenyan Drill"],
    "Mizrahi": ["Mizrahi", "Mizrachi", "Yemeni Diwan"],
    "Reggaeton": ["Reggaeton", "Reggaton"]
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

EXCLUSION_LIST = [g.lower() for g in ["Drum N Base", "Drum N Bass", "DrumNBase", "Uk Dnb", "Dubstep", "Psytrance"]]

# Pre-process routing dictionary for O(1) case-insensitive lookup
REVERSE_ROUTING = {}
for target, genres in GENRE_ROUTING_DICT.items():
    for g in genres:
        REVERSE_ROUTING[g.lower()] = target

# --- API Helper Functions ---

@st.cache_data(show_spinner=False)
def parse_description(description):
    """Parses description to extract ordered genres and track counts using flexible regex."""
    if not description:
        return []
    
    # 1. Normalize unicode (fraktur/italic letters to ASCII, superscript to numbers)
    text = unicodedata.normalize('NFKC', description)
    
    # 2. Extract just the genre section (usually bounded by | symbols or newlines)
    if '|' in text:
        parts = text.split('|')
        target_part = parts[0]
        # Find the part that looks most like a genre list
        for part in parts:
            if '♩' in part or any(str(i) in part for i in range(10)):
                target_part = part
                break
        text = target_part
        
    # 3. Dynamic Regex Extraction
    parsed = []
    # Match words/symbols for genre, followed by optional spaces and then digits
    matches = re.findall(r'([A-Za-z \-\/\,&]+?)\s*([\d]+)', text)
    
    for genre_str, count_str in matches:
        clean_genre = genre_str.strip(', /|♩ ')
        if clean_genre:
            parsed.append({"genre": clean_genre, "count": int(count_str)})
            
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
    """Determines if a track has Hebrew characters or an Israeli artist."""
    if not track_obj:
        return False
        
    # Check track name for Hebrew characters
    track_name = track_obj.get('name', '')
    if re.search(r'[\u0590-\u05FF]', track_name):
        return True
        
    # Check artists
    artists = track_obj.get('artists', [])
    for artist in artists:
        artist_name = artist.get('name', '')
        if not artist_name:
            continue
            
        # Check artist name for Hebrew characters
        if re.search(r'[\u0590-\u05FF]', artist_name):
            return True
            
        # Check against parsed set 
        if artist_name.strip().lower() in ISRAELI_ARTISTS_SET:
            return True
            
    return False

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

if 'target_existing_uris' not in st.session_state:
    st.session_state['target_existing_uris'] = load_target_existing_uris(sp)

# 1. Visual Pre-Flight Check
st.subheader("1. Identified Target Source Playlists")
st.markdown("Playlists are correctly sorted chronologically by their `Aum#`.")
with st.expander("View Source Playlists", expanded=False):
    df_sources = pd.DataFrame([{"Aum#": int(re.search(r'Aum#(20[1-9]|2[1-8][0-9]|29[0-7])', p['name']).group(1)), "Name": p['name'], "Tracks": p['tracks']['total'], "Description": p.get('description', '')} for p in all_source_playlists])
    st.dataframe(df_sources, use_container_width=True)

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
    
    start_idx = 0 if simulate_only else st.session_state["current_playlist_index"]
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
        tracks = get_all_playlist_tracks(sp, playlist['id'])
        
        track_index = 0
        for p_genre in parsed_genres:
            genre_name = p_genre['genre'].lower()
            count = p_genre['count']
            
            target = REVERSE_ROUTING.get(genre_name)
            is_excluded = genre_name in EXCLUSION_LIST
            
            if not target and not is_excluded:
                global_anomalies.add(genre_name)
                
            for _ in range(count):
                if track_index >= len(tracks):
                    break
                
                item = tracks[track_index]
                track_index += 1
                
                track_obj = item.get('track')
                if not track_obj or not track_obj.get('uri') or track_obj['uri'].startswith('spotify:local:'):
                    total_null += 1
                    track_name = track_obj.get('name', 'Unknown') if track_obj else 'Unknown Data'
                    audit_log.append({"Source Playlist": plist_name, "Parsed Genre": genre_name, "Target Playlist": "None", "Track URI": "None", "Track Name": track_name, "Action Taken": "Skipped (Null URI)"})
                    continue
                
                uri = track_obj['uri']
                track_name = track_obj.get('name', 'Unknown')
                
                if is_excluded:
                    total_dropped += 1
                    audit_log.append({"Source Playlist": plist_name, "Parsed Genre": genre_name, "Target Playlist": "Drop List", "Track URI": uri, "Track Name": track_name, "Action Taken": "Dropped (Exclusion List)"})
                    continue
                    
                israeli_bonus_matched = False
                
                if target:
                    if uri in local_existing_uris[target]:
                        total_skipped += 1
                        audit_log.append({"Source Playlist": plist_name, "Parsed Genre": genre_name, "Target Playlist": target, "Track URI": uri, "Track Name": track_name, "Action Taken": "Skipped Duplicate"})
                    else:
                        target_staged_tracks[target].append(uri)
                        local_existing_uris[target].add(uri)
                        audit_log.append({"Source Playlist": plist_name, "Parsed Genre": genre_name, "Target Playlist": target, "Track URI": uri, "Track Name": track_name, "Action Taken": "Appended"})

                # --- Parallel Israeli Music Routing ---
                if target != "Israeli Music" and is_israeli_track(track_obj):
                    israeli_target = "Israeli Music"
                    israeli_bonus_matched = True
                    if uri in local_existing_uris[israeli_target]:
                        audit_log.append({"Source Playlist": plist_name, "Parsed Genre": genre_name, "Target Playlist": israeli_target, "Track URI": uri, "Track Name": track_name, "Action Taken": "Skipped Duplicate (Bonus: Israeli Music)"})
                    else:
                        target_staged_tracks[israeli_target].append(uri)
                        local_existing_uris[israeli_target].add(uri)
                        audit_log.append({"Source Playlist": plist_name, "Parsed Genre": genre_name, "Target Playlist": israeli_target, "Track URI": uri, "Track Name": track_name, "Action Taken": "Appended (Bonus: Israeli Music)"})
                        
                if not target and not israeli_bonus_matched:
                    audit_log.append({"Source Playlist": plist_name, "Parsed Genre": genre_name, "Target Playlist": "None", "Track URI": uri, "Track Name": track_name, "Action Taken": "Unmapped / Ignored"})

    progress_bar.progress(1.0, text="Process Complete!")
    return audit_log, target_staged_tracks, global_anomalies

# 2. Phase A: Simulation
st.subheader("2. Phase A: Dry-Run Simulation")
st.markdown("Run a simulation on exactly 2 playlists to verify mapping integrity before committing database POST operations.")

if st.button("Run Mapping Simulation (Dry-Run)", type="primary"):
    with st.spinner("Processing simulation..."):
        sim_log, staged, anomalies = process_mapping(simulate_only=True, batch_size=2)
        st.session_state['simulation_done'] = True
        
        sim_df = pd.DataFrame(sim_log)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Tracks Staged", sum(len(v) for v in staged.values()))
        col2.metric("Duplicates Skipped", len(sim_df[sim_df['Action Taken'].str.contains('Skipped Duplicate')]) if not sim_df.empty else 0)
        col3.metric("Unmapped Anomalies", len(anomalies))
        
        st.markdown("**Simulation Audit Log Preview:**")
        st.dataframe(sim_df, use_container_width=True)
        
        if anomalies:
            st.warning(f"Unmapped Genres Detected: {', '.join(anomalies)}")

# 3. Phase B: Execution (Batch Control Panel)
if st.session_state['simulation_done']:
    st.divider()
    st.subheader("3. Phase B: Execute Batch Migration")
    st.markdown(f"**Current Progress:** Processed `{st.session_state['current_playlist_index']}` out of `{len(all_source_playlists)}` playlists.")
    
    remaining = len(all_source_playlists) - st.session_state['current_playlist_index']
    st.progress(st.session_state['current_playlist_index'] / len(all_source_playlists))
    
    if remaining > 0:
        c1, c2, c3 = st.columns(3)
        batch_to_run = 0
        
        if c1.button("Process Next 5 Playlists", disabled=(remaining==0)):
            batch_to_run = min(5, remaining)
        if c2.button("Process Next 10 Playlists", disabled=(remaining==0)):
            batch_to_run = min(10, remaining)
        if c3.button("Process All Remaining", disabled=(remaining==0)):
            batch_to_run = remaining
            
        if batch_to_run > 0:
            batch_log, staged_tracks, full_anomalies = process_mapping(simulate_only=False, batch_size=batch_to_run)
            
            with st.status(f"Uploading Batch ({batch_to_run} playlists)...", expanded=True) as status:
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
            st.session_state["current_playlist_index"] += batch_to_run
            st.session_state["cumulative_audit_log"].extend(batch_log)
            
            # Update local URIs so the next batch knows about the tracks we just appended
            for tgt, uris in staged_tracks.items():
                st.session_state['target_existing_uris'][tgt].update(uris)
                
            st.success(f"Successfully processed playlists index {start_num} through {start_num + batch_to_run - 1}!")
            st.rerun()
    else:
        st.success("All playlists have been completely migrated!")

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
