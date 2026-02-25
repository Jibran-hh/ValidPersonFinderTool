# Valid Person Finder

Valid Person Finder is a small web tool that discovers the most likely person for a given **company + designation** using only public web data.

- **Backend**: Python / FastAPI
- **Search sources**: DuckDuckGo (via `duckduckgo-search` + HTML fallback) and Bing HTML
- **Frontend**: Single‑page, responsive HTML/CSS/JS

---

## Running the project

### 1. Create and activate a virtual environment (recommended)

```bash
python -m venv .venv
source .venv/bin/activate         # macOS / Linux
.\.venv\Scripts\activate          # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the FastAPI backend

```bash
cd backend
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://127.0.0.1:8000`.

You can quickly verify it with:

```bash
curl http://127.0.0.1:8000/health
```

### 4. Open the frontend

You can either:

- Open `frontend/index.html` directly in your browser, or
- Serve it with a small static server (e.g. VS Code Live Server, `python -m http.server`, etc.).

If you serve it on `http://127.0.0.1:5500`, the CORS settings are already configured.

---

## How it works (high level)

- **Query construction**
  - Takes a `company` and `designation` as input.
  - Expands the designation into a set of **aliases** (e.g. `CEO` → `["CEO", "Chief Executive Officer", "Founder & CEO", ...]`).
  - Builds multiple query variations such as:
    - `"Meta" "CEO" site:linkedin.com`
    - `"Meta" "Chief Executive Officer"`

- **Search API integration**
  - Uses `duckduckgo-search` (no API key) for one source.
  - Uses a lightweight HTML scrape of Bing SERP as a second, distinct search source.
  - Results are de-duplicated across providers.

- **Name extraction & validation**
  - Inspects result titles and snippets for patterns such as `Name – Title – Company`.
  - Extracts a **full name**, splits it into first and last name, and records:
    - `current_title`
    - `source_url` and a `source_type` (LinkedIn snippet, Wikipedia, news, generic web, etc.)
  - Assigns a **confidence score** based on:
    - Trusted domains (LinkedIn, Wikipedia, Crunchbase, major news)
    - Presence of the company name
    - Presence of designation aliases
    - Cross-validation across providers (same name seen multiple times increases confidence).

- **Output**
  - Returns a structured JSON:
    - `best_match`: top-ranked `PersonMatch`
    - `candidates`: all merged candidates with confidence scores
    - `raw_results`: raw search results from DuckDuckGo + Bing
    - `normalized_designation_aliases`: aliases actually used
    - `message`: short human-readable status

The frontend displays:

- A **highlighted card** for the best match with confidence pill, title, and source link.
- A scrollable list of **all candidates**.
- A collapsible section with the **raw JSON**.

---

## Environment variables / API keys

This implementation uses:

- `duckduckgo-search` (no API key needed)
- HTML scraping of **DuckDuckGo** and **Bing**

If you decide to add other search APIs (e.g. Brave Search, LangSearch), place any API keys in a `.env` file (e.g. `BRAVE_API_KEY=...`) and **never commit the `.env` file** to version control.

---

## Notes for the reviewers

- The code is intentionally **modular**:
  - `backend/aliases.py` – designation alias logic.
  - `backend/search_providers.py` – individual search sources.
  - `backend/name_extractor.py` – extraction heuristics and confidence scoring.
  - `backend/app.py` – FastAPI wiring and JSON API.
- The UI is focused on being:
  - **Clean, modern, and presentable**.
  - Usable even when the result is low-confidence (the message and confidence pills make this explicit).

You can easily extend this to:

- Add an agentic layer (e.g. LangChain) that reruns searches when confidence is low.
- Plug in additional search sources (Brave Search, LangSearch, etc.).

