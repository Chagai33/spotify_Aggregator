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
    pool = sorted(tracks_data, key=lambda x: x.get("Algorithm Score 🏅", 0), reverse=True)
    result = []
    
    current_track = pool.pop(0)
    result.append(current_track)
    recent_artists = [a for a in current_track.get("Artist", "").split(", ")]
    
    def camelot_distance(c1, c2):
        if c1 == "Unknown" or c2 == "Unknown": return 0
        try:
            num1, letter1 = int(c1[:-1]), c1[-1]
            num2, letter2 = int(c2[:-1]), c2[-1]
            
            dist_num = min(abs(num1 - num2), 12 - abs(num1 - num2))
            dist_letter = 1 if letter1 != letter2 else 0
            
            if dist_num == 0 and dist_letter == 0: return 0
            if (dist_num == 1 and dist_letter == 0) or (dist_num == 0 and dist_letter == 1): return 1
            return dist_num + dist_letter
        except:
            return 2
            
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
            
            for a in candidate.get("Artist", "").split(", "):
                if a in recent_artists:
                    penalty += 50
                    
            energy_diff = abs(current_energy - c_energy)
            if energy_diff > 0.2:
                penalty += 50
                
            cam_dist = camelot_distance(current_camelot, c_camelot)
            if cam_dist == 0:
                penalty -= 10
            elif cam_dist == 1:
                penalty -= 5
            else:
                penalty += (cam_dist * 5)
                
            flow_score = score - penalty
            if flow_score > best_flow_score:
                best_flow_score = flow_score
                best_idx = i
                
        current_track = pool.pop(best_idx)
        result.append(current_track)
        
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
