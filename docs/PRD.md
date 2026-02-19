# PRD: Vicioso Perfume Recommender (AI / ML)

## 1) Overview

Build an application that recommends perfumes from Vicioso Studios by combining:
- The full product catalog (scraped from the website)
- A user's purchase history (perfumes already bought)
- The user's current intent/preferences:
  - desired scent notes
  - scent families (e.g., Blumig, Frisch, Süß/Gourmandig, Holzig, etc.)
  - occasions (office, date, everyday, evening, etc.)
  - moods (cosy, elegant, energetic, calm, etc.)
  - strength / intensity preference (soft → strong)

The system produces a ranked list of perfumes with explanations ("recommended because: …") and optional filters.

## 2) Goals

- Scrape and normalize Vicioso product data into a structured dataset.
- Provide high-quality recommendations that match user inputs and also consider what they already own.
- Support cold start (no purchases yet) using pure content-based matching.
- Provide transparent explanations: notes overlap, family match, intensity match, "similar to what you own".
- Make it easy to iterate: retrain or re-rank without rewriting the whole system.

## 3) Non-goals (for v1)

- Predicting exact longevity/projection from chemistry (not reliably available).
- External data enrichment (Fragrantica/Parfumo) unless explicitly added later.
- User-to-user collaborative filtering at scale (only one/few users initially).

## 4) Target Users / Personas

### Returning Buyer
Has bought multiple perfumes and wants similar vibes or a "next best" addition.

### Goal-based Shopper
"Need a fresh office scent that isn't too strong."

### Explorer
"I want something new but still within gourmand / warm."

## 5) Core User Stories

- As a user, I can select perfumes I already bought and get "similar but not duplicates" recommendations.
- As a user, I can input 2–6 notes and get perfumes ranked by note overlap and closeness.
- As a user, I can choose scent families and see matching perfumes ranked higher.
- As a user, I can choose occasion + mood and get context-appropriate suggestions.
- As a user, I can set strength (subtle/medium/strong) and the recommender adapts.
- As a user, I can see why each perfume was recommended.

## 6) Data Sources

### 6.1 Catalog pages
Collection listing pages: product name, URL, price, maybe rating count.
Filters show available categories (e.g., Geschlecht, Duftfamilie, Moleküle).

### 6.2 Product detail pages (per perfume)
Extract:
- Name
- Description text
- Perfume notes: top notes, middle notes, base notes (present on product pages).
- Ingredients (optional)
- Any tags/collection info if present
- Image URL(s)
- Product handle / ID (from URL)

## 7) Data Model (Storage Schema)

Create a perfumes table (or parquet/JSONL) with:
- `perfume_id` (stable ID derived from URL handle)
- `name`
- `url`
- `price_min`, `price_max` (if variants)
- `gender_tags` (array)
- `scent_families` (array)
- `molecule_tags` (array) (e.g., Iso E Super variants if present)
- `notes_top` (array of strings)
- `notes_middle` (array)
- `notes_base` (array)
- `notes_all` (array = union + position metadata)
- `description` (string)
- `image_urls` (array)
- `last_scraped_at`

Create a user_profile object:
- `owned_perfume_ids` (array)
- `liked_notes` / `disliked_notes` (arrays, optional)
- `preferred_families` (array)
- `occasion` (string or multi)
- `moods` (array)
- `strength_preference` (enum: subtle/medium/strong)
- `constraints` (e.g., exclude certain families/notes)

## 8) Scraping Requirements

- Respect robots.txt and reasonable rate limits (e.g., 1 request/sec, retries with backoff).
- Crawl pagination for "Alle Parfums" (shows ~122 products).
- For each product URL, fetch and parse:
  - notes sections (Top/Middle/Base)
  - description
  - tags/categories if present
- Store raw HTML snapshots optionally (debugging).
- Provide a "scrape refresh" command to update the dataset.

**Acceptance criteria:**
- ≥ 98% of products successfully parsed with name + url + notes_all.
- Notes parsed into structured arrays with minimal noise.

## 9) Recommendation Approach (v1 → v2)

### 9.1 v1: Hybrid Content-Based Scoring (recommended for first version)

Compute a final score as a weighted combination:

**A) Note similarity**
- Jaccard or cosine similarity on note sets
- Extra weight if note matches in the same position (top vs base)

**B) Scent family match**
- Boost score if user-selected families match

**C) Similar-to-owned**
- Compute similarity to each owned perfume; use max or average similarity
- Penalize recommending perfumes already owned

**D) Occasion/mood/strength**
- Create rule-based mappings first:
  - "office" favors fresh/clean, lower intensity
  - "evening/date" allows warm/sweet/woody, higher intensity
- Strength can be approximated initially:
  - Heuristic from concentration keywords if present, otherwise map families (e.g., "Warm/Orientalisch/Süß" tends stronger). Keep as a tunable heuristic.

**Output:**
- Top N recommendations (default N=10)
- Explanations listing top reasons (matched notes, matched family, similar to X)

### 9.2 v2: Embeddings + Learned Re-ranker

- Create text embeddings from: name + description + notes + families
- Use nearest-neighbor search (FAISS or similar)
- Add a lightweight learned ranking model once you collect feedback clicks/likes:
  - Inputs: similarity features + user preferences
  - Label: clicked / liked / purchased

## 10) Feedback Loop

Collect optional signals:
- user clicks a perfume
- user likes/dislikes a recommendation
- user purchases (manual input)

Store as events:
- `event_type`, `perfume_id`, `timestamp`, `context` (occasion/mood/strength)

Use these to:
- adjust user profile (boost liked notes/families)
- evaluate recommendation quality over time

## 11) API / Interfaces

Provide a simple local API (or module functions):

### Endpoints / functions

**GET /perfumes** (filters: family, notes contains, etc.)

**POST /recommendations**
- body: user_profile + optional filters + N
- returns: ranked list with explanation fields

**Recommendation response item:**
```
perfume_id, name, url, image_url
score
reasons (array of strings)
matched_notes (array)
matched_families (array)
similar_to_owned (e.g., top 1–2 owned matches)
```

## 12) UI (Minimal v1)

**Inputs:**
- owned perfumes (multi-select)
- desired notes (free text chips)
- preferred families (multi-select)
- occasion (dropdown)
- mood (multi-select chips)
- strength slider (subtle ↔ strong)

**Output:**
- card list of recommendations with:
  - image, name, families, key notes
  - "Why this?" expandable section
  - controls to exclude notes/families

## 13) Evaluation Metrics

**Offline (no user feedback yet):**
- Coverage: % of catalog recommendable
- Diversity: avoid recommending 10 near-identical scents
- Novelty: avoid duplicates of owned items
- Sanity checks: recommendations match chosen families/notes

**Online (when feedback exists):**
- CTR on recommended items
- Like rate
- "Save to wishlist" rate
- Repeat usage

## 14) Technical Requirements

- **Language:** Python (preferred)
- **Storage:** SQLite or parquet/JSONL for catalog; SQLite for events
- **Reproducible pipeline:**
  1. scrape
  2. parse/clean
  3. build features
  4. recommend
- **Logging:** scraping success rate, parse failures, model scoring debug

## 15) Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Site structure changes | Write robust selectors + fallback parsing + tests |
| Strength estimation is fuzzy | Make it optional, start heuristic, improve with feedback |
| Small personal dataset | Content-based first; add learning once enough feedback exists |

## 16) Milestones

### M1 – Scraper + Dataset
Scrape all listing pages + product pages; store normalized dataset.

### M2 – v1 Recommender
Hybrid scoring + explanations; CLI or simple web UI.

### M3 – Feedback
Like/dislike + click tracking; basic personalization.

### M4 – v2 Embeddings
Add semantic embeddings + nearest-neighbor search; optional re-ranker.
