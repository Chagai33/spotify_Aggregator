# 🏗️ Aum.Music Advanced Architecture & Algorithms

This document outlines the deep technical decisions, mathematical models, and architectural bypasses implemented in the Aum.Music Aggregator, transitioning it from a simple ETL pipeline into a musicological sequencing engine.

---

## 1. Advanced Algorithmic Sequencing

Instead of a naive "sort by score descending" approach (which leads to listener fatigue as high-energy tracks clump together), we built a Sequencing Engine that models professional DJ set flows.

### Musicological Data Integration
The system fetches deep acoustic metrics from the Spotify Audio Features API:
*   **Energy:** A float from `0.0` to `1.0`.
*   **Key & Mode:** Integer representations of Pitch Class and Major/Minor modality.

Since Spotify strictly limits Audio Features API calls, we implemented a **Local Caching Layer**. The system checks a local JSON file (`audio_features_cache.json`) for historical tracks before executing the API call, drastically reducing payload size and risk of rate-limiting.

### Camelot Wheel Translation
To ensure playlists flow harmonically without dissonant key clashes, we implemented a conversion algorithm that translates Spotify's standard integers into the industry-standard **Camelot System** (e.g., `8A`, `9B`).

```python
camelot_wheel = {
    (0, 1): '8B', (1, 1): '3B', (2, 1): '10B', (3, 1): '5B', # ...
}
```

### The Three Sequencing Strategies
Users can select between three strategies, or rely on an **Auto-Selector** that analyzes playlist length and variance:

1.  **🎢 The Rollercoaster (Energy Arcs)**
    *   **Logic:** Maps a mathematical Sine Wave across the length of the playlist.
    *   **Execution:** Calculates the absolute distance between a track's real Energy and the Sine Wave's ideal Energy at that specific index. High-scoring tracks are magnetized to the physical peaks of the wave, ensuring natural ebb and flow.
2.  **🔀 Hit Interleave (Anchor Discovery)**
    *   **Logic:** Classic radio programming technique.
    *   **Execution:** Alternates between an "Anchor" track (High Score/Popularity) and a "Discovery" track (Lower Score), weaving back and forth to keep listener attention engaged through unfamiliar material.
3.  **🌊 Flow Optimizer (Anti-Clumping & Harmonics)**
    *   **Logic:** Strict state-machine sequencing modeling a continuous club mix.
    *   **Execution:** 
        *   Prevents any two adjacent tracks from having an Energy delta greater than `0.2`.
        *   Computes the "Distance" on the Camelot Wheel between the last track and the candidate pool, applying massive multipliers to tracks in the exact same or adjacent harmonic key.

---

## 2. Global Score Normalization & Curator Override

Because scores originate from vastly different sources (Spotify Popularity `0-100`, Custom Sub-Genre Weights `1-5`), they are incompatible.

### Global Min-Max Scaler
We run a final validation pass that compresses every algorithm's internal scoring output into a normalized `0` to `100` percentage score. This provides human-readable confidence scores when viewing the DataGrid.

### Curator Boost
Machine logic must yield to human preference. The system natively looks for a `"S3 My Favorite"` playlist in the user's library.
If a track in the sequence pipeline exists in that playlist, it receives a strict **1.4x (40%) Score Multiplier**, guaranteeing that the curator's "anchor" songs will forcefully bubble up the algorithm's decisions.

---

## 3. Distributed In-Memory Caching & Rate-Limit Bypassing

Scaling to library sizes of over 1,000+ playlists exposed strict limitations in both the Spotify API and the Streamlit UX.

### Bypassing Hashing Lockups (Pickle Freezing)
Originally, global API fetches were wrapped in `@st.cache_data`. We discovered that hashing 1,000+ massive Spotipy dictionary payloads to determine Cache invalidation caused the Python engine to hard-freeze (memory lockup).
We refactored this by dropping `@st.cache_data` for heavy external objects, moving the core payload to `st.session_state`. This means 1,000+ playlists sit instantly accessible in native RAM across all UI tabs, reducing wait times between clicks to `0ms`.

### Handling Spotipy HTTP 429 Sleep-Loops
When stress-testing, Spotify's API threw an **HTTP 429 (Too Many Requests)** error with a `Retry-After: 71000s`.
By default, the `Spotipy` requests library obeys this header and executes `time.sleep(71000)` on the backend—silently hanging the web server for 20 hours.

**The Fix:**
```python
st.session_state['sp'] = spotipy.Spotify(auth_manager=sp_oauth, requests_timeout=5, status_retries=0)
```
We stripped `status_retries=0` from the initializer, enforcing strict failure. The app now elegantly intercepts `spotipy.SpotifyException`, catches the 429, and renders a graceful `st.error` on the UI before formally halting the execution, guaranteeing the web server never hangs.
