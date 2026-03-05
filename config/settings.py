import os
import re
from dotenv import load_dotenv

# Load environment variables (Client ID, Secret, Redirect URI)
load_dotenv()

SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

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
