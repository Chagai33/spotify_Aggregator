import os
import streamlit as st
import pandas as pd
import re
import time
import unicodedata
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import html
import json
from datetime import datetime

# Load environment variables (Client ID, Secret, Redirect URI)
load_dotenv()

TARGET_PLAYLISTS = {
    "♩ Israeli Hip Hop": "1Ycl9i5uMtniDKs0jKvJOe",
    "♩ Reggae": "3obWJRscGGN4QvmeLZK7US",
    "♩ Israeli Music": "70y6Euzv1eUaYgR6Qzoo2r",
    "♩ 𝘐𝘴𝘳𝘢𝘦𝘭𝘪 𝘗𝘰𝘱 ": "0JJ482EewHlIGNnKu9xGXa",
    "♩ Country, Indie": "6QZz84AaYPlD1ALgrVacP4",
    "♩ Melodic House": "7F8Bea5phhXrDwAx5rETPg",
    "♩ Hip Hop, Rap": "3GiWLHwdkZU9VQ4i1aagWa",
    "♩ Afrobeats": "1XyXp1FRHBRnvxmmhT5Sz6",
    "♩ Mizrahi": "1zcEZURYYKMCvs4rpTB6ti",
    "♩ Reggaeton": "09QZH7Nlj4vS9Paur6Srcm",
    "♩ s3 למיין": "4qYupj1n5KASzFohe5RSmH"
}

GENRE_ROUTING_DICT = {
    "♩ Israeli Hip Hop": ["Israeli Hip Hop", "Israeli Rap"],
    "♩ Reggae": ["Reggae", "Modern Reggae", "Reggae Rock", "Indie Reggae", "West Coast Reggae"],
    "♩ Israeli Music": ["Israeli Music", "Israeli Indie", "Indie IL", "Israeli"],
    "♩ 𝘐𝘴𝘳𝘢𝘦𝘭𝘪 𝘗𝘰𝘱 ": ["Israeli Pop"],
    "♩ Country, Indie": ["Country", "Country Pop", "Indie", "Indie Pop", "American Indie", "Indie Folk", "Pop, Folk", "Folk, Pop", "Indie Soul", "Soul Indie", "Retro soul", "Modern Indie Folk", "Modern Indie", "Indie Rock", "Alternative Indie", "Alternative Pop", "Acoustic Soul", "Folk Acoustic", "Folk-Soul", "Pop Soul", "Lo-Fi", "R And B", "R&B", "Rendb", "RB", "Soul", "Electro Chil", "Electro Chill", "Indie Modern Funk", "Acoustic Folk", "Folk", "Acoustic", "Pop", "Alternative Indie, Rock", "Meditation", "indie rock, pop", "indie soul, country", "indie folk", "lofi", "folk", "acoustic"],
    "♩ Melodic House": ["Melodic House", "Melodic Techno", "Tropical House", "Organic House", "Indie House", "Tech House", "Techno House", "Bass House", "Base House", "Funky Bass House", "Edm", "EDM House", "Electro House", "Funky House", "Fusion House", "Electropop", "Brazilian Edm", "Mix House", "Groove House", "House", "House Techno", "Techno", "Tech, Bass House", "Groove Metal", "bass / melodic house"],
    "♩ Hip Hop, Rap": ["Hip Hop", "Rap", "Hip Hop, Rap", "Rap, Hip Hop", "UG Hip Hop", "Underground Hip Hop", "UG Hip Pop", "UG Rap", "Trap", "Dark Trap", "Latin Trap", "Bass Trap", "Hip Pop", "East Coast Hip Hop", "Multigenre Rap", "Dfw Rap", "London Rap", "Westcoast Rap", "West Coast Rap", "Drift Phonk", "Hip Hop Rap", "Hip Pop / Trap", "NYC"],
    "♩ Afrobeats": ["Afrobeats", "Afrobeat", "Dancehall", "Kenyan Drill", "Dancehall Blend"],
    "♩ Mizrahi": ["Mizrahi", "Mizrachi", "Yemeni Diwan"],
    "♩ Reggaeton": ["Reggaeton", "Reggaton"],
    "♩ s3 למיין": ["Mix", "Mix Gener", "Mixed Genres", "Spacial Intro"]
}

# --- Parallel Routing Configuration ---
STATS_FILE = "playlist_insights_cache.json"
AUDIO_FEATURES_CACHE = "audio_features_cache.json"

# --- Harmonic System Mapping (Spotify Key/Mode -> Camelot) ---
# Spotify Key: 0=C, 1=C#...11=B. Mode: 0=Minor, 1=Major
CAMELOT_DICT = {
    (0, 1): "8B",  # C Major
    (0, 0): "5A",  # C Minor
    (1, 1): "3B",  # Db Major
    (1, 0): "12A", # C# Minor
    (2, 1): "10B", # D Major
    (2, 0): "7A",  # D Minor
    (3, 1): "5B",  # Eb Major
    (3, 0): "2A",  # D# Minor
    (4, 1): "12B", # E Major
    (4, 0): "9A",  # E Minor
    (5, 1): "7B",  # F Major
    (5, 0): "4A",  # F Minor
    (6, 1): "2B",  # F# Major
    (6, 0): "11A", # F# Minor
    (7, 1): "9B",  # G Major
    (7, 0): "6A",  # G Minor
    (8, 1): "4B",  # Ab Major
    (8, 0): "1A",  # G# Minor
    (9, 1): "11B", # A Major
    (9, 0): "8A",  # A Minor
    (10, 1): "6B", # Bb Major
    (10, 0): "3A", # Bb Minor
    (11, 1): "1B", # B Major
    (11, 0): "10A" # B Minor
}

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

def get_all_user_playlists(_sp):
    """Fetches ALL user playlists with pagination to bypass 1000+ limits. Includes safety limits."""
    playlists = []
    offset = 0
    max_fetches = 100 # Safety limit: max 5000 playlists
    fetches = 0
    
    while fetches < max_fetches:
        try:
            results = _sp.current_user_playlists(limit=50, offset=offset)
            if not results or not results.get('items'):
                break
            playlists.extend(results['items'])
            if len(results['items']) < 50:
                break
            offset += len(results['items'])
            fetches += 1
        except spotipy.SpotifyException as e:
            if e.http_status == 429:
                st.error("⛔ Spotify Rate Limit Reached! (Error 429: Too Many Requests). Spotify has temporarily blocked this application's access. Please wait before refreshing.")
                st.stop()
            else:
                st.error(f"Spotify API Error fetching playlists: {e}")
                st.stop()
        except Exception as e:
            st.error(f"Error fetching playlists at offset {offset}: {e}")
            st.stop()
            
    return playlists

def get_target_source_playlists(all_playlists):
    """Filters all playlists to find the target source ones (Week#200-300) and sorts them numerically."""
    # Matches Week# followed by 200 up to 300
    pattern = re.compile(r'Week#(2[0-9]{2}|300)')
    matched = []
    for p in all_playlists:
        if p and p.get('name') and pattern.search(p['name']):
            # Extract number for precise sorting
            num = int(pattern.search(p['name']).group(1))
            matched.append((num, p))
            
    # Sort by the extracted Week# number
    matched.sort(key=lambda x: x[0])
    return [p for num, p in matched]

def fetch_audio_features_with_cache(sp, uris):
    """
    Fetches audio features for a list of URIs. uses a local JSON cache to avoid rate limits.
    Spotify limits audio_features to 100 URIs per request.
    """
    if not uris:
        return {}
        
    cache_path = AUDIO_FEATURES_CACHE
    cache_data = {}
    
    # 1. Load existing cache
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
        except Exception:
            cache_data = {}
            
    # 2. Identify missing URIs
    missing_uris = [uri for uri in uris if uri not in cache_data]
    
    # 3. Fetch missing URIs in batches of 100
    if missing_uris:
        # Deduplicate to prevent API errors
        missing_uris = list(set(missing_uris)) 
        
        for i in range(0, len(missing_uris), 100):
            batch = missing_uris[i:i+100]
            try:
                features = sp.audio_features(batch)
                
                # Zip and update cache
                for uri, feature in zip(batch, features):
                    if feature: # Sometimes spotify returns None for local files
                        cache_data[uri] = {
                            "energy": feature.get("energy", 0.5),
                            "key": feature.get("key", 0),
                            "mode": feature.get("mode", 1)
                        }
                    else:
                        # Dummy fallback to prevent repeated API calls
                        cache_data[uri] = {"energy": 0.5, "key": 0, "mode": 1}
                        
            except Exception as e:
                st.error(f"Error fetching audio features: {e}")
                
        # 4. Save updated cache back to disk
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=4)
        except Exception:
            pass
            
    # 5. Build and return the requested sub-dictionary
    result = {uri: cache_data.get(uri) for uri in uris if uri in cache_data}
    return result

def get_all_playlist_tracks(sp, playlist_id):
    """Fetches ALL tracks from a playlist, handling pagination and preventing hard loops."""
    tracks = []
    offset = 0
    max_fetches = 100 # Safety limit: Max 10,000 tracks per playlist
    fetches = 0
    
    while fetches < max_fetches:
        try:
            results = sp.playlist_items(playlist_id, limit=100, offset=offset)
            if not results or not results.get('items'):
                break
            tracks.extend(results['items'])
            if len(results['items']) < 100:
                break
            offset += len(results['items'])
            fetches += 1
        except spotipy.exceptions.SpotifyException as e:
            # Handle specific Spotify API errors (e.g., 404, rate limits)
            print(f"Spotify API Error fetching tracks for {playlist_id} at offset {offset}: {e}")
            break
        except Exception as e:
            print(f"Unexpected error fetching tracks for {playlist_id} at offset {offset}: {e}")
            break
            
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

sp = st.session_state['sp']



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
    if 'global_playlists' in st.session_state:
        del st.session_state['global_playlists']
    st.rerun()

# 1. Fetch Global Playlists ONCE into session state to prevent API exhaustion and UI hanging
if 'global_playlists' not in st.session_state:
    with st.spinner("Fetching 1000+ playlists from Spotify API..."):
        st.session_state['global_playlists'] = get_all_user_playlists(sp)

# 2. Derive Target Playlists from global state
@st.cache_data(show_spinner=False)
def filter_source_playlists(all_pls):
    return get_target_source_playlists(all_pls)

all_source_playlists = filter_source_playlists(st.session_state['global_playlists'])

if not all_source_playlists:
    st.error("No source playlists matching `Week#200-...` found.")
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

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(['🎧 Phase 1: Migration Engine', '🧹 Phase 2: Cross-Playlist Cleanup', '🛡️ Phase 3: Backup & Restore', '📊 Phase 4: Global Playlists Insights', '🌟 Phase 5: SEO & Popularity Optimizer', '🏷️ Phase 6: Rename Season', '🔍 Phase 7: Season Orphan Validator'])

with tab1:
    # 1. Visual Pre-Flight Check
    st.subheader("1. Identified Target Source Playlists")
    st.markdown("Playlists are correctly sorted chronologically by their `Week#`.")
    with st.expander("View Source Playlists", expanded=False):
        df_sources = pd.DataFrame([{"Week#": int(re.search(r'Week#(2[0-9]{2}|300)', p['name']).group(1)), "Name": p['name'], "Tracks": p['tracks']['total'], "Description": p.get('description', '')} for p in all_source_playlists])
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
        
        col_ok, col_refresh, col_cancel = st.columns([2, 2, 4])
        
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
                
        with col_refresh:
            if st.button("🔄 Refresh Preview"):
                batch_to_run = st.session_state['pending_batch_size']
                with st.spinner(f"Simulating Batch ({batch_to_run} playlists) again..."):
                    batch_log, staged_tracks, full_anomalies = process_mapping(simulate_only=True, batch_size=batch_to_run)
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

with tab2:
    st.header("🧹 Cross-Playlist Cleanup Utility")
    st.markdown("Safely remove tracks from **Playlist A** that already exist in **Playlist B**.")
    
    # Fetch all user playlists to populate dropdowns
    all_user_playlists = st.session_state['global_playlists']
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
                
                if not overlap:
                    st.success("✅ No overlapping tracks found! Playlist A is fully independent of Playlist B.")
                
    if st.session_state.get('cleanup_uris'):
        st.divider()
        st.warning(f"Found {len(st.session_state['cleanup_uris'])} overlapping tracks ready for review.")
        
        # Build DataFrame and add the exclusion boolean column
        df_overlap = pd.DataFrame(st.session_state['cleanup_overlap'])
        if "Keep (Don't Delete)" not in df_overlap.columns:
            df_overlap.insert(0, "Keep (Don't Delete)", False)
            
        st.markdown("**Review the overlapping tracks below. Check the box if you want to KEEP the track in Playlist A.**")
        
        # Display as interactive data editor
        edited_df = st.data_editor(
            df_overlap,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Keep (Don't Delete)": st.column_config.CheckboxColumn(
                    "Keep (Don't Delete)",
                    help="Select this to protect the track from being deleted.",
                    default=False,
                )
            }
        )
        
        col_exec1, col_exec2 = st.columns([1, 4])
        
        # Filter URIs based on user selection in the data_editor
        final_uris_to_delete = edited_df[edited_df["Keep (Don't Delete)"] == False]["URI"].tolist()
        
        with col_exec1:
            if st.button(f"🗑️ Delete {len(final_uris_to_delete)} Tracks", type="primary"):
                if not final_uris_to_delete:
                    st.warning("No tracks selected for deletion (All tracks are marked to Keep).")
                else:
                    with st.spinner("Deleting selected tracks from Playlist A..."):
                        playlist_id_to_clean = st.session_state['cleanup_a_id']
                        
                        # Delete in chunks of 100
                        for chunk in chunk_list(final_uris_to_delete, 100):
                            sp.playlist_remove_all_occurrences_of_items(playlist_id_to_clean, chunk)
                            time.sleep(0.5)
                            
                    st.success(f"Successfully deleted {len(final_uris_to_delete)} overlapping tracks!")
                    
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

with tab4:
    st.header("📊 Phase 4: Global Playlists Insights")
    st.markdown("View comprehensive statistics for all your playlists. Since fetching follower counts for hundreds of playlists takes time, use 'Basic Sync' for a quick overview or 'Deep Refresh' for specific items.")
    
    STATS_FILE = "playlist_insights_cache.json"
    
    # Load cache from file if it exists and session state is empty
    if 'all_playlists_stats' not in st.session_state:
        if os.path.exists(STATS_FILE):
            try:
                with open(STATS_FILE, 'r', encoding='utf-8') as f:
                    st.session_state['all_playlists_stats'] = json.load(f)
            except Exception:
                st.session_state['all_playlists_stats'] = {}
        else:
            st.session_state['all_playlists_stats'] = {}
        
    col_basic, col_deep = st.columns(2)
    with col_basic:
        if st.button("⚡ Fast Sync (All Playlists, No Followers)", type="primary"):
            with st.spinner("Fetching basic playlist metadata..."):
                all_pls = get_all_user_playlists(sp)
                new_stats = {}
                for p in all_pls:
                    # Keep existing follower count if we already fetched it deeply, else 'N/A'
                    existing = st.session_state['all_playlists_stats'].get(p['id'], {})
                    followers = existing.get("Followers", "N/A")
                    
                    new_stats[p['id']] = {
                        "ID": p['id'],
                        "Playlist Name": p['name'],
                        "Followers": followers,
                        "Total Tracks": p['tracks']['total'],
                        "Public": "Yes" if p['public'] else "No",
                        "Collaborative": "Yes" if p['collaborative'] else "No",
                        "Description": html.unescape(p.get('description', '') or ''),
                        "Owner": p['owner']['display_name']
                    }
                st.session_state['all_playlists_stats'] = new_stats
                
                # Save to disk
                with open(STATS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(new_stats, f, indent=2, ensure_ascii=False)
                    
                st.success(f"Successfully loaded and cached {len(new_stats)} playlists!")
                time.sleep(1)
                st.rerun()

    with col_deep:
        if st.button("🐢 Deep Sync (All Playlists + Followers - VERY SLOW)"):
            if not st.session_state['all_playlists_stats']:
                st.warning("Please do a 'Fast Sync' first to load the playlist IDs.")
            else:
                total_pls = len(st.session_state['all_playlists_stats'])
                progress_bar = st.progress(0, text="Deep syncing all playlists...")
                
                for idx, (p_id, stats) in enumerate(st.session_state['all_playlists_stats'].items()):
                    try:
                        p_full = sp.playlist(p_id)
                        stats["Followers"] = p_full['followers']['total']
                        stats["Total Tracks"] = p_full['tracks']['total']
                        stats["Public"] = "Yes" if p_full['public'] else "No"
                        stats["Collaborative"] = "Yes" if p_full['collaborative'] else "No"
                        stats["Description"] = html.unescape(p_full.get('description', '') or '')
                        stats["Owner"] = p_full['owner']['display_name']
                        
                        # Polite API rate limiting
                        time.sleep(0.2)
                    except Exception:
                        stats["Followers"] = "Error"
                        time.sleep(1) # Back off on error
                    
                    progress_bar.progress((idx + 1) / total_pls, text=f"Deep syncing... ({idx + 1}/{total_pls})")
                
                # Save to disk after full deep sync
                with open(STATS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(st.session_state['all_playlists_stats'], f, indent=2, ensure_ascii=False)
                    
                progress_bar.empty()
                st.success("Deep sync complete! Insights cached locally.")
                time.sleep(1)
                st.rerun()

    st.divider()
    
    if st.session_state['all_playlists_stats']:
        st.subheader("Targeted Refresh")
        # Ensure we have a mapping from name -> id for the selectbox
        # We append the ID to handle if playlists have identical names
        name_to_id = {f"{v['Playlist Name']} ({k[:8]})": k for k, v in st.session_state['all_playlists_stats'].items()}
        selected_name = st.selectbox("Search and select a specific playlist to Deep Refresh:", options=list(name_to_id.keys()))
        
        if st.button("🔄 Deep Refresh Selected"):
            selected_id = name_to_id[selected_name]
            with st.spinner(f"Fetching full metadata..."):
                try:
                    p_full = sp.playlist(selected_id)
                    st.session_state['all_playlists_stats'][selected_id].update({
                        "Followers": p_full['followers']['total'],
                        "Total Tracks": p_full['tracks']['total'],
                        "Public": "Yes" if p_full['public'] else "No",
                        "Collaborative": "Yes" if p_full['collaborative'] else "No",
                        "Description": html.unescape(p_full.get('description', '') or ''),
                        "Owner": p_full['owner']['display_name']
                    })
                    
                    # Save to disk after individual update
                    with open(STATS_FILE, 'w', encoding='utf-8') as f:
                        json.dump(st.session_state['all_playlists_stats'], f, indent=2, ensure_ascii=False)
                        
                    st.success("Updated successfully, and cache saved!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to refresh: {e}")
                    
        st.divider()
        
        st.subheader("Playlists View")
        search_query = st.text_input("🔍 Filter Table by Playlist Name:").strip().lower()
        
        df_data = list(st.session_state['all_playlists_stats'].values())
        if search_query:
            df_data = [d for d in df_data if search_query in str(d["Playlist Name"]).lower()]
            
        if df_data:
            df = pd.DataFrame(df_data)
            df_display = df.drop(columns=["ID"]) if "ID" in df.columns else df
            st.dataframe(df_display, use_container_width=True)
            st.caption(f"Showing {len(df_data)} playlists.")
        else:
            st.info("No playlists match your search.")
    else:
        st.info("Click 'Fast Sync' above to load your playlists.")

# --- SEQUENCE STRATEGY FUNCTIONS (PHASE 5) ---
import math
import random

def apply_rollercoaster_wave_sort(tracks_data):
    if not tracks_data: return []
    n = len(tracks_data)
    w = max(1, n // 40) # 1 wave per ~40 tracks
    
    # 1. Generate Sine Wave targets for Energy (0.2 to 0.9 range)
    # T(i) = 0.55 + 0.35 * sin(2*pi * W * i/N)
    targets = []
    for i in range(n):
        target_energy = 0.55 + 0.35 * math.sin(2 * math.pi * w * i / max(1, n))
        targets.append({'index': i, 'target_energy': target_energy})
        
    # We want to fill the most extreme targets first (highest peaks and lowest valleys)
    # so we give them the best matching songs.
    targets.sort(key=lambda x: abs(x['target_energy'] - 0.55), reverse=True)
    
    # We will pick from a pool of tracks
    pool = list(tracks_data)
    result = [None] * n
    
    for t_data in targets:
        target_idx = t_data['index']
        target_eng = t_data['target_energy']
        
        best_track_idx = -1
        best_cost = float('inf')
        
        # We need a Weighted Distance Function:
        # Cost = |TargetEnergy - TrackEnergy|*100 - TrackScore
        # Lower cost is better. We want Energy match, but we also want High Scores.
        for j, track in enumerate(pool):
            track_eng = track.get("Energy ⚡", 0.5)
            track_score = track.get("Algorithm Score 🏅", 0)
            
            cost = abs(target_eng - track_eng) * 100.0 - track_score
            if cost < best_cost:
                best_cost = cost
                best_track_idx = j
                
        # Assign best track to this slot, remove from pool
        result[target_idx] = pool.pop(best_track_idx)
        
    return [r for r in result if r is not None]

def apply_hit_interleave_sort(tracks_data):
    if not tracks_data: return []
    sorted_tracks = sorted(tracks_data, key=lambda x: x.get("Algorithm Score 🏅", 0), reverse=True)
    n = len(sorted_tracks)
    
    split_a = max(1, int(n * 0.2))
    split_b = max(1, int(n * 0.7))
    
    tier_a = sorted_tracks[:split_a]
    tier_b = sorted_tracks[split_a:split_b]
    tier_c = sorted_tracks[split_b:]
    
    random.shuffle(tier_a)
    random.shuffle(tier_b)
    random.shuffle(tier_c)
    
    result = []
    pattern = ['A', 'B', 'B', 'C', 'B', 'B']
    idx = 0
    
    while len(result) < n:
        ptn = pattern[idx % len(pattern)]
        idx += 1
        
        if ptn == 'A' and tier_a: result.append(tier_a.pop(0))
        elif ptn == 'B' and tier_b: result.append(tier_b.pop(0))
        elif ptn == 'C' and tier_c: result.append(tier_c.pop(0))
        elif tier_a: result.append(tier_a.pop(0))
        elif tier_b: result.append(tier_b.pop(0))
        elif tier_c: result.append(tier_c.pop(0))
            
    return result

def apply_csp_flow_sort(tracks_data):
    if not tracks_data: return []
    # Advanced Greedy approach: Minimize artist clumping AND ensure harmonic/energy flow
    pool = sorted(tracks_data, key=lambda x: x.get("Algorithm Score 🏅", 0), reverse=True)
    result = []
    
    # 1. Cold Start: Always start with the absolute best track
    current_track = pool.pop(0)
    result.append(current_track)
    recent_artists = [a for a in current_track.get("Artist", "").split(", ")]
    
    # Helper for Camelot Distance
    def camelot_distance(c1, c2):
        if c1 == "Unknown" or c2 == "Unknown": return 0
        try:
            # Parse '8A' -> 8, 'A'
            num1, letter1 = int(c1[:-1]), c1[-1]
            num2, letter2 = int(c2[:-1]), c2[-1]
            
            # Distance on the wheel (1 to 12)
            dist_num = min(abs(num1 - num2), 12 - abs(num1 - num2))
            # Distance in mode (A to B)
            dist_letter = 1 if letter1 != letter2 else 0
            
            # Perfect match: 0
            if dist_num == 0 and dist_letter == 0: return 0
            # Compatible match (same mode, adjacent num OR same num, different mode): 1
            if (dist_num == 1 and dist_letter == 0) or (dist_num == 0 and dist_letter == 1): return 1
            # Clash: > 1
            return dist_num + dist_letter
        except:
            return 2 # Default clash penalty if parsing fails
            
    while pool:
        best_idx = 0
        best_flow_score = -float('inf')
        lookahead = min(20, len(pool))
        
        current_energy = current_track.get("Energy ⚡", 0.5)
        current_camelot = current_track.get("Camelot 🎵", "Unknown")
        
        for i in range(lookahead):
            candidate = pool[i]
            score = candidate.get("Algorithm Score 🏅", 0)
            c_energy = candidate.get("Energy ⚡", 0.5)
            c_camelot = candidate.get("Camelot 🎵", "Unknown")
            
            penalty = 0
            
            # Constraint 1: Artist Clumping
            for a in candidate.get("Artist", "").split(", "):
                if a in recent_artists:
                    penalty += 50
                    
            # Constraint 2: Energy Flow (Don't drop/spike more than 0.2)
            energy_diff = abs(current_energy - c_energy)
            if energy_diff > 0.2:
                penalty += 50
                
            # Constraint 3: Harmonic Flow (Camelot Wheel)
            cam_dist = camelot_distance(current_camelot, c_camelot)
            if cam_dist == 0:
                penalty -= 10 # Bonus for perfect key match
            elif cam_dist == 1:
                penalty -= 5  # Bonus for adjacent harmonic match
            else:
                penalty += (cam_dist * 5) # Penalty for harmonic clash
                
            flow_score = score - penalty
            if flow_score > best_flow_score:
                best_flow_score = flow_score
                best_idx = i
                
        current_track = pool.pop(best_idx)
        result.append(current_track)
        
        # Update artist history window (Keep last 10 artists)
        for a in current_track.get("Artist", "").split(", "):
            recent_artists.append(a)
        if len(recent_artists) > 10:
            recent_artists = recent_artists[-10:]
            
    return result

def auto_select_sort(tracks_data):
    n = len(tracks_data)
    if n < 30:
        return apply_hit_interleave_sort(tracks_data), "Hit Interleave (Short Playlist)"
        
    scores = [t.get("Algorithm Score 🏅", 0) for t in tracks_data]
    if not scores: return tracks_data, "None"
    
    variance = max(scores) - min(scores)
    
    all_artists = set()
    for t in tracks_data:
        for a in t.get("Artist", "").split(", "):
            all_artists.add(a)
    
    density = n / max(1, len(all_artists))
    
    if density > 3.0:
        return apply_csp_flow_sort(tracks_data), "Optimize for Flow (High Artist Density)"
    elif variance > 50 and n >= 80:
        return apply_rollercoaster_wave_sort(tracks_data), "The Rollercoaster (High Variance)"
    else:
        return apply_hit_interleave_sort(tracks_data), "Hit Interleave (Balanced)"

with tab5:
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

with tab6:
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
                        get_all_user_playlists.clear()
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

with tab7:
    st.header("🔍 Phase 7: Season Orphan Validator")
    st.markdown("Find and move tracks that infiltrated Master Playlists without being in any `Week#200-300` season playlists.")
    
    # State flags for Phase 7
    if "p7_orphans" not in st.session_state:
        st.session_state["p7_orphans"] = []
    if "p7_master_id" not in st.session_state:
        st.session_state["p7_master_id"] = None
    if "p7_dest_id" not in st.session_state:
        st.session_state["p7_dest_id"] = None
        
    all_user_playlists_p7 = st.session_state['global_playlists']
    playlist_options_p7 = {p['name']: p['id'] for p in all_user_playlists_p7}
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Master Playlist (To Clean)")
        st.caption("Select the official playlist to evaluate and clean.")
        master_dropdown = st.selectbox("Select Master Playlist", options=list(playlist_options_p7.keys()), key="p7_master_sel")
        master_url = st.text_input("Or enter Spotify URL for Master Playlist", key="p7_master_url", placeholder="https://open.spotify.com/playlist/...")
    
    with col2:
        st.subheader("Destination Playlist (Vault)")
        st.caption("Orphaned tracks will be moved here.")
        dest_dropdown = st.selectbox("Select Destination Playlist", options=list(playlist_options_p7.keys()), key="p7_dest_sel")
        dest_url = st.text_input("Or enter Spotify URL for Destination", key="p7_dest_url", placeholder="https://open.spotify.com/playlist/...")

    master_id = extract_playlist_id(master_url) or playlist_options_p7.get(master_dropdown)
    dest_id = extract_playlist_id(dest_url) or playlist_options_p7.get(dest_dropdown)
    
    if st.button("🔍 Scan & Verify Orphans", type="primary"):
        if not master_id or not dest_id:
            st.error("Invalid Playlist IDs.")
        elif master_id == dest_id:
            st.error("Master and Destination playlists cannot be the same.")
        else:
            with st.spinner("Fetching Season Source of Truth (Week#200-300)..."):
                # Fetch Playlist Names for UI Transparency (especially if URL was used)
                try:
                    master_name = sp.playlist(master_id)['name']
                    dest_name = sp.playlist(dest_id)['name']
                    st.info(f"**Targeting Master Playlist:** `{master_name}`")
                    st.info(f"**Moving Orphans To:** `{dest_name}`")
                except Exception as e:
                    st.error("Could not fetch playlist details. Make sure the URLs are public and valid.")
                    st.stop()
            
                # Check Cache First
                if "p7_season_uris" in st.session_state:
                    season_uris = st.session_state["p7_season_uris"]
                    st.success(f"Loaded Source of Truth from Memory Cache: {len(season_uris)} unique tracks.")
                else:    
                    # Find all season playlists
                    pattern = re.compile(r'Week#(2[0-9]{2}|300)')
                    season_playlists = [p for p in all_user_playlists_p7 if p and p.get('name') and pattern.search(p['name'])]
                    
                    if not season_playlists:
                        st.error("No season playlists (Week#...) found to build the Source of Truth.")
                        season_uris = set()
                    else:
                        season_uris = set()
                        # Aggregate ALL URIs from the season
                        progress_text = "Downloading Season Tracks. Please wait..."
                        my_bar = st.progress(0, text=progress_text)
                        
                        for i, p in enumerate(season_playlists):
                            tracks = get_all_playlist_tracks(sp, p['id'])
                            for item in tracks:
                                t = item.get('track')
                                if t and t.get('uri'):
                                    # Avoid adding Local Files to our truth source
                                    if not t['uri'].startswith('spotify:local:'):
                                        season_uris.add(t['uri'])
                            my_bar.progress((i + 1) / len(season_playlists), text=progress_text)
                        
                        # Save to Cache
                        st.session_state["p7_season_uris"] = season_uris
                        st.success(f"Built Source of Truth (And Cached for Session): {len(season_uris)} unique tracks found in Season.")
                
                if season_uris:
                    with st.spinner("Analyzing Master Playlist against Source of Truth..."):
                        master_tracks = get_all_playlist_tracks(sp, master_id)
                        orphans = []
                        orphan_uris = []
                        
                        for item in master_tracks:
                            t = item.get('track')
                            if not t or not t.get('uri'):
                                continue
                            
                            uri = t['uri']
                            # Skip local files completely, we can't move them easily anyway
                            if uri.startswith('spotify:local:'):
                                continue
                                
                            if uri not in season_uris:
                                orphans.append({
                                    "Track Name": t.get('name', 'Unknown'),
                                    "Artist": ", ".join(arr['name'] for arr in t.get('artists', [])),
                                    "Added At": item.get('added_at', 'Unknown'),
                                    "URI": uri
                                })
                                if uri not in orphan_uris:
                                    orphan_uris.append(uri)
                        
                        st.session_state["p7_orphans"] = orphans
                        st.session_state["p7_master_id"] = master_id
                        st.session_state["p7_dest_id"] = dest_id
                    
                        if not orphans:
                            st.success("✅ Perfect Architecture! 0 Orphans found. All tracks in the Master Playlist belong to this season.")

    if st.session_state.get("p7_orphans"):
        orphans = st.session_state["p7_orphans"]
        st.divider()
        st.warning(f"🚨 Found {len(orphans)} orphaned tracks! They are in the Master Playlist but were never in a weekly Release Radar.")
        
        st.dataframe(pd.DataFrame(orphans), use_container_width=True)
        
        col_exec1, col_exec2 = st.columns([1, 4])
        with col_exec1:
            if st.button(f"🚚 Move {len(orphans)} Tracks to Vault", type="primary"):
                with st.spinner("Moving Orphans safely..."):
                    uris_to_move = [o["URI"] for o in orphans]
                    source_id = st.session_state["p7_master_id"]
                    dest_vault_id = st.session_state["p7_dest_id"]
                    
                    # 1. Protection: Check what is already in the Vault so we don't duplicate
                    vault_tracks = get_all_playlist_tracks(sp, dest_vault_id)
                    vault_existing_uris = {item['track']['uri'] for item in vault_tracks if item.get('track') and item['track'].get('uri')}
                    
                    filtered_uris_to_add = [uri for uri in uris_to_move if uri not in vault_existing_uris]
                    
                    # 2. Add to Vault
                    if filtered_uris_to_add:
                        for chunk in chunk_list(filtered_uris_to_add, 100):
                            sp.playlist_add_items(dest_vault_id, chunk)
                            time.sleep(0.5)
                            
                    # 3. Remove cleanly from Master Playlist
                    for chunk in chunk_list(uris_to_move, 100):
                        sp.playlist_remove_all_occurrences_of_items(source_id, chunk)
                        time.sleep(0.5)
                        
                st.success(f"Execution Complete: {len(uris_to_move)} orphans were cleaned. {len(filtered_uris_to_add)} were added to the Vault (the rest were already there).")
                st.session_state["p7_orphans"] = []
                st.session_state["p7_master_id"] = None
                st.session_state["p7_dest_id"] = None
                time.sleep(3)
                st.rerun()
                
        with col_exec2:
            if st.button("❌ Cancel & Reset Tracker"):
                st.session_state["p7_orphans"] = []
                st.session_state["p7_master_id"] = None
                st.session_state["p7_dest_id"] = None
                st.rerun()
