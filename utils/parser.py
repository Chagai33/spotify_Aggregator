import re
import html
import unicodedata
import streamlit as st

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
