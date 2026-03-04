# Multi-Year Retrospective Ranking Strategies

## Overview
This document outlines advanced algorithms and weighting formulas for sorting and ranking Spotify tracks in a multi-year season retrospective playlist (e.g., 2024-2026). Relying solely on Spotify's native `track_popularity` metric is flawed for multi-year playlists because it heavily penalizes older tracks. These algorithms aim to balance current popularity, artist authority, and track age to surface true era-defining hits.

## Data Extraction Requirements (Spotify API)
- `track_popularity` ($T_p$): Integer (0-100)
- `artist_popularity` ($A_p$): Integer (0-100)
- `release_date`: ISO 8601 string (Convert to `months_age`)

## Algorithms

### Approach 1: Authority-Adjusted Decay (Linear)
**Best for rapid deployment and transparency.** Uses artist authority to filter "one-hit wonders" and adds a linear "age bonus."

```python
# Cap age to prevent old tracks from dominating indefinitely (e.g., max 36 or 60 months)
capped_age = min(months_age, 60)
# W_t=0.5, W_a=0.3, W_d=0.2 (Tuning weights)
raw_score = (track_pop * 0.5) + (artist_pop * 0.3) + (capped_age * 0.2)
```

**Pros:**
- Simplest to implement with datetime and pandas.
**Cons:**
- High risk of over-promoting mediocre older tracks if $W_d$ is too aggressive.

### Approach 2: Longitudinal Z-Score Hybrid (Recommended)
**Best for statistical rigor.** Normalizes tracks within their release year to identify "Best in Class" regardless of current decay.

```python
from scipy.stats import norm

# 1. Group by release_year
# 2. Calculate Z-Score for each track: z = (x - μ) / σ
# 3. Convert Z-Score to Percentile (0.0 to 1.0) to correctly merge with artist_pop fraction
track_percentile = norm.cdf(z_track)

# 4. Final Ranking:
raw_score = (track_percentile * 0.7) + ((artist_pop / 100) * 0.3)
```

**Pros:**
- Effectively kills "Recency Trap"; ensures hits from 2024 outrank mediocre 2026 tracks.
**Cons:**
- Requires $\geq 15$ tracks per year for standard deviation ($\sigma$) validity.

### Approach 3: Logarithmic Momentum Index
**Best for mimicking production recommendation engines** (Reddit/YouTube). Uses diminishing returns for age.

```python
import math

# Use log/ln to handle exponential distribution of native scores
raw_score = math.log10(track_pop + 1) * (1 + (artist_pop / 100)) + math.log(months_age + 1)
```

**Pros:**
- Prevents older songs from dominating solely via age; rewards consistent "staying power."
**Cons:**
- Sensitive to input scaling; requires clipping or careful outlier management.

### 4: Mandatory Global Normalization (Min-Max Scaling)
**Crucial Scale Match:** The algorithms above produce `raw_score` values in completely different mathematical scales (e.g., Approach 2 is max 1.0, Approach 3 is usually under 10). To ensure the *Auto-Sort Decision Matrix* and constraints (like CSP) function correctly, the final array of scores *must* be normalized to a standard `0-100` scale before sequencing.

```python
# Min-Max Scaler
min_val = min(raw_scores)
max_val = max(raw_scores)

normalized_scores = [
    ((s - min_val) / (max_val - min_val)) * 100 if max_val > min_val else 100
    for s in raw_scores
]
```

## Critical API Note (Feb 2026)
> **Warning**: The popularity field may return null or be restricted for "Development Mode" apps on Spotify. If this occurs, "Extended Quota Mode" or a third-party proxy (e.g., Soundcharts API) might be required.

---

# Multi-Year Playlist Sequencing Strategies

Based on behavioral data and audio streaming UX principles, ranking algorithms should not just be used to "pin the top X tracks."

## 1. The Flaw of "Pinning the Top"
* **Violates the Peak-End Rule and Serial Position Effect:** Front-loading a playlist with the highest-scored tracks ensures the listening session concludes in an unsequenced "graveyard" of low-tier tracks. This anchors the listener's final cognitive evaluation to the weakest audio.
* **Accelerates Cognitive Fatigue and Skip Rates:** Unstructured audio in the tail end causes unpredictable fluctuations. Behavioral data shows 25% of tracks are skipped within 5 seconds. High-friction transitions in the unsequenced tail trigger rapid succession skipping.
* **Destroys Mathematical Playlist Coherence:** Clustering the most popular tracks at the beginning creates the lowest possible coherence. It builds a disjointed "greatest hits" block that strips the remaining 80-90% of the playlist of necessary anchors.

## 2. The Optimal Playlist Architectures

### Sinusoidal Energy Wave (The Rollercoaster)
Maps track scores to an oscillating mathematical wave to create emotional arcs of tension and release.
* **Strategy:** Use a basic sine wave to map ideal sequence scores. Sort both the 300 tracks and the calculated ideal target indices descending by score. Perform a greedy assignment by mapping the highest-scoring actual track to the index that demands the highest wave peak.
* **Use Case:** Ideal for long road trips or vibe-based playlists needing gradual buildup, satisfying peaks, and graceful cooldowns to prevent sensory burnout.

### Stratified Interleaving (Hit Interleave)
Divides the tracklist into distinct quality tiers and sequences them using a deterministic, repeating round-robin pattern to anchor unfamiliar tracks with guaranteed hits.
* **Strategy:** Sort all tracks and slice into 3 arrays (e.g., A=Top, B=Mid, C=Low). Shuffle internally. Iterate through a repeating pattern (e.g., `[A, B, B, C, B, B]`). Pop tracks from the corresponding queue until empty.
* **Use Case:** Best for "Vault" or discovery playlists where users need an introduction to older deep cuts or unfamiliar music without losing engagement.

### Constraint Satisfaction Programming (Flow Optimization)
Evaluates the sequence globally by defining mathematical penalties for jarring transitions and duplicate artists, using optimization to minimize the playlist's "violation cost."
* **Strategy:** Define penalties ($+10$ for score drops $> 40$, $+50$ for identical artists within 5 tracks). Use Hill Climbing optimization—randomly swap two tracks, calculate the new total cost, keep the swap if the cost lowers, revert if it increases.
* **Use Case:** Optimal for background ambient music and automated radio, yielding organically "human-sounding" sequences by eliminating strict monotonic decreases.

## 3. UI / UX Recommendation
A professional interface abstracts math into intent-based toggles. The dropdown menu should present:
* **The Rollercoaster (Energy Arcs)** – Executes the Sinusoidal Energy Wave.
* **Hit Interleave (Anchor Discovery)** – Executes Stratified Interleaving.
* **Optimize for Flow (Smooth Transitions)** – Executes Constraint Satisfaction Programming.
* **Auto-Select Best Strategy** – Runs the Decision Matrix below.

---

## 4. Auto-Sort Decision Matrix (Pipeline)
When providing an "Auto-Select" feature, the algorithm must dynamically route the playlist to the correct sorting strategy to prevent mathematical failures. This router avoids two major pitfalls:
1. **The Micro-Playlist Trap:** Prevents short playlists (e.g., 25 tracks) from triggering "high artist density" penalties just because an artist appears twice.
2. **The Score Variance Blind Spot:** Prevents "Hit Interleave" from failing if a user provides a playlist where *every* track has an identical or very high score (meaning it cannot be split into tiers).

### Router Logic / Pseudo-Code
```python
# 1. Data Gathering
density = max_artist_count / total_tracks
variety = unique_artists / total_tracks
score_variance = max_score - min_score

# 2. Rule 1: Emergency Check (Density, Variety, Variance)
# If the playlist has extreme repetition (and isn't tiny), or if all tracks are scored identically.
if (total_tracks > 40 and (density > 0.08 or variety < 0.30)) or score_variance < 15:
    return apply_csp_flow_sort(playlist_tracks)

# 3. Rule 2: Long Playlist Management
elif total_tracks > 150:
    return apply_rollercoaster_wave_sort(playlist_tracks)

# 4. Rule 3: Default Distribution
else:
    return apply_hit_interleave_sort(playlist_tracks)
```
