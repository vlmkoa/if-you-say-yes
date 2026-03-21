# App flow and how to test it

## 1. How the app flows (high level)

```
┌─────────────┐     ┌──────────────────────────────────────────────────────────┐
│   Browser   │     │                     Docker / Host                         │
│             │     │                                                           │
│  localhost  │────▶│  Frontend (Next.js :3000)                                │
│  :3000      │     │    • Home: interaction form + link to dashboard          │
│             │     │    • /reagent: upload image → Python backend              │
│             │     │    • Dashboard: substance grid (server-fetched)            │
└──────┬──────┘     └───────┬─────────────────────────────┬────────────────────┘
       │                    │                             │
       │  GET /health       │  GET /api/substances         │
       │  GET /interaction  │  (server-side)               │
       │  POST /reagent/analyze                         │
       ▼                    ▼                             ▼
       │             Python backend (:8000)         core-api (:8080)
       │             • Neo4j driver                 • Spring Boot + JPA
       │             • GET /health                  • PostgreSQL
       │             • GET /interaction            • GET /api/substances
       │             • POST /reagent/analyze ──► OpenAI GPT-4o (vision) *
       │                    │                      • POST /api/substances/sync
       │                    ▼                      • GET /actuator/health
       │             Neo4j (AuraDB or local)
       │             • Substance nodes
       │             • INTERACTS_WITH edges
       │
       └────────────────────┴─────────────────────────────┘

* Reagent flow: LLM returns structured JSON (colors + reagent hints); substance
  suggestions are computed locally from backend/reagent_chart_data.py (no LLM).
```

**Data sources (optional, for loading data):**
- **TripSit combos** → script writes into **Neo4j** (interactions).
- **PsychonautWiki + OpenFDA** → script POSTs to **core-api /api/substances/sync** (dosage + adverse events in PostgreSQL).

---

## 2. How a user interacts with the app

### Entry point
User opens **http://localhost:3000** (or http://localhost if using the nginx profile).

### Home page
1. Sees title “if-you-say-yes” and short description.
2. Sees link to **Dashboard** (substance profiles).
3. Sees **“Check drug interaction”** section with two search inputs (Substance A, Substance B) and a **“Check interaction”** button.
4. **Health check:** On load, the frontend calls the Python backend **GET /health**.  
   - If Neo4j is **unavailable:** an amber banner says “Interaction check temporarily unavailable” and the button is disabled.  
   - If **available:** no banner; user can type and submit.
5. User picks or types two substances and clicks **“Check interaction”**.
6. Frontend calls **GET /interaction?drug_a=…&drug_b=…** on the Python backend; backend queries **Neo4j**.
7. User sees one of:
   - **Dangerous** (red): risk + mechanism.
   - **Caution** (yellow): caution + mechanism.
   - **No significant risk** (green).
   - **No known interaction** (green): no edge in the graph.
   - **Error / 503:** “Interaction service temporarily unavailable” (Neo4j down or unreachable).

### Dashboard
1. User clicks **“Dashboard”** → **http://localhost:3000/dashboard**.
2. Next.js **server** fetches **GET /api/substances** from **core-api** (which reads **PostgreSQL**).
3. User sees a grid of **substance profiles** (name, half-life, bioavailability, standard dosage; plus dosage/adverse JSON if synced).
4. If core-api or PostgreSQL is down: user sees **“Substance list temporarily unavailable. The database may be offline.”**

### Reagent test (`/reagent`)
1. User opens **http://localhost:3000/reagent**.
2. Optionally selects a **reagent test** from the dropdown and/or types context (e.g. “Marquis”, “column Md”) if the photo doesn’t show the kit name.
3. User uploads an image; the browser **POST**s multipart data to **`POST /reagent/analyze`** on the Python backend (`NEXT_PUBLIC_BACKEND_URL`, default `http://localhost:8000`).
4. The backend calls **OpenAI GPT-4o (vision)** to extract **observable** data only (hex color(s), optional **reagent method** / chart column, visible text). It does **not** ask the model to name an unknown street sample as a specific drug.
5. The backend **resolves** which chart column applies (vision `method` → optional form `reagent` → text in `prompt` → OCR labels when there is a single swatch).
6. For each color, it runs **deterministic** RGB distance matching against **`backend/reagent_chart_data.py`** for that reagent only, then returns ranked substance rows + disclaimers.

**Requirements:** `OPENAI_API_KEY` on the backend. Without it, `/reagent/analyze` returns **503**.

### Optional: Nginx
If you run with **nginx** (port 80), the user goes to **http://localhost**. Nginx routes **/** to the frontend and **/api/backend/** to the Python backend. The interaction form must be built with `NEXT_PUBLIC_BACKEND_URL=http://localhost/api/backend` so it talks to the backend through Nginx.

---

## 2b. Where LLMs are used (and where they are not)

### Summary

| Use case | Model | Code | When it runs |
|----------|-------|------|----------------|
| **Reagent image analysis** | **gpt-4o** (vision) | `backend/reagent_vision.py` → `extract_vision_from_image()` | User uploads an image on `/reagent`; backend sends image + instructions to OpenAI; model returns **JSON** (hexes, optional `method` per swatch, `labels`, `description`). |
| **Category fallback** | **gpt-4o-mini** (text) | `scripts/assign_categories.py` | Optional **offline** script: if mapping/heuristics can’t classify a substance name, script asks the LLM to pick one of the fixed categories. |
| **Interaction reference helper** | **gpt-4o-mini** (text) | `scripts/populate_interaction_references.py` | Optional **offline** script: suggests a “similar” TripSit substance for Postgres `interactionReference`. |

**Not using an LLM:** drug–drug **GET /interaction** (Neo4j only), dashboard **GET /api/substances**, core-api CRUD, reagent **substance ranking** (pure math vs `REAGENT_CHART`), Neo4j loaders.

### Reagent flow (LLM + deterministic) — detail

```
User image + optional text
        │
        ▼
┌───────────────────┐
│  FastAPI          │  POST /reagent/analyze
│  backend/main.py  │  • multipart: image, prompt, reagent
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│  OpenAI API       │  chat.completions, model=gpt-4o,
│  (vision)         │  user message = text + image_url (base64 data URI)
└─────────┬─────────┘
          │ assistant message: JSON string
          ▼
┌───────────────────┐
│  reagent_vision   │  _parse_vision_json() — strip ``` fences, validate
│                   │  resolve_reagent_for_color_entry() — Marquis, Md, …
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│  reagent_chart_   │  match_hex_to_drugs_for_reagent(hex, method)
│  data.py          │  Euclidean distance in RGB; top-k % scores
└─────────┬─────────┘
          │
          ▼
   JSON response → frontend ReagentChat (bar chart + disclaimers)
```

**Design intent:** the LLM is a **perception + structure** step (what color is visible, what column header text appears). **Identification against the chart** is **deterministic** so behavior is auditable and doesn’t rely on the model inventing drug IDs.

**Environment:** `OPENAI_API_KEY` in the process environment (e.g. project root `.env` for Docker backend). Quota/rate errors surface as **503** with a billing hint.

**Optional offline LLM scripts** also read `OPENAI_API_KEY`; they never receive user-uploaded reagent photos.

---

## 3. How to test it

### 3.1 Start the stack

```powershell
cd c:\Users\volem\Documents\CS\projects\ifyousayyes
docker compose up -d --build
```

Wait until all are up: `docker compose ps` (postgres, core-api, frontend, backend).

- **Frontend:** http://localhost:3000  
- **Python backend:** http://localhost:8000  
- **core-api:** http://localhost:8080  

### 3.2 Test without loading data (smoke test)

1. **Home**
   - Open http://localhost:3000.
   - If Neo4j env is **not** set: you should see the amber “Interaction check temporarily unavailable” banner and a disabled button.
   - If Neo4j **is** set but empty: banner may disappear; clicking “Check interaction” for two drugs usually returns **“No known interaction”** (404 from backend).

2. **Dashboard**
   - Open http://localhost:3000/dashboard.
   - With an empty DB you should see **“No substance profiles found”** or an empty grid (no error).

3. **Backend health**
   - GET http://localhost:8000/health  
   - No Neo4j: **503**. With Neo4j reachable: **200** `{"status":"ok","neo4j":"available"}`.

4. **core-api health**
   - GET http://localhost:8080/actuator/health  
   - Expect **200** when PostgreSQL is up.

### 3.3 Load Neo4j (interaction data)

1. Put Neo4j credentials in **`.env`** (see RUN.md):
   ```env
   NEO4J_URI=neo4j+s://…
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=…
   ```
2. Restart backend: `docker compose up -d backend`.
3. From project root (with `.env` loaded):
   ```powershell
   python scripts/load_tripsit_to_neo4j.py
   ```
4. **Test interaction**
   - Open http://localhost:3000.
   - Ensure no “temporarily unavailable” banner (or it disappears after a moment).
   - Enter e.g. **caffeine** and **alcohol** (or two names from TripSit combos), click “Check interaction”.
   - You should get a result (e.g. Caution, Low Risk, etc.) instead of “No known interaction”.

### 3.4 Load core-api (substance profiles)

1. With **core-api** and **postgres** running:
   ```powershell
   python scripts/sync_substances_to_core_api.py
   ```
   (Uses default list: caffeine, ibuprofen, alcohol, lsd, mdma.)

2. **Test dashboard**
   - Open http://localhost:3000/dashboard.
   - You should see a grid of substances with name, half-life, bioavailability, and (if synced) dosage/adverse data.

3. **Test API directly**
   - GET http://localhost:8080/api/substances?page=0&size=5  
   - Expect JSON with `content`, `totalElements`, etc.

### 3.5 Test failure behavior

1. **Neo4j down**
   - Stop Neo4j or remove/break credentials and restart backend.
   - Open http://localhost:3000: amber banner + disabled button.
   - GET http://localhost:8000/health → **503**.

2. **core-api / PostgreSQL down**
   - Stop core-api (or postgres).
   - Open http://localhost:3000/dashboard: message **“Substance list temporarily unavailable. The database may be offline.”**
   - GET http://localhost:8080/actuator/health → **503** (if the app is down or DB is down and actuator reflects it).

### 3.6 Reagent analyze (LLM + chart)

**Needs:** backend up, **`OPENAI_API_KEY`** set, `pip install openai` in the environment running the backend.

1. Open http://localhost:3000/reagent.
2. (Recommended for a single tube with no header) choose **Marquis** (or another reagent) from the dropdown, then upload a small JPEG/PNG of a colored liquid or a chart crop.
3. Expect JSON back with `colors[]` (each with `hex`, optional `method`, `matches[]`, or `needs_reagent` if the test type couldn’t be resolved).
4. If you get **503** and “OPENAI_API_KEY”: add the key to `.env` and `docker compose up -d backend` (or restart `uvicorn`).

**Direct API (curl example):** multipart `image=@photo.jpg`, optional `prompt=Marquis`, optional `reagent=Marquis`.

### 3.7 One command to test APIs (no UI)

From project root:

```powershell
python scripts/test_api_gets.py
```

This hits **GET /interaction** (caffeine + alcohol) and **GET /api/substances** and prints status and a short summary.

### 3.8 Curl-like backend checks (Neo4j)

To verify the Python backend and Neo4j from the host (no browser):

```powershell
python scripts/check_backend.py
```

This GETs **/health** and **/interaction?drug_a=caffeine&drug_b=alcohol** and prints status and body. If **/health** is 200, Neo4j is reachable from the backend. If the **frontend** still shows “Interaction check temporarily unavailable”, the browser cannot reach the backend (wrong URL, different host, or try a hard refresh). Use the same hostname in the browser as in `NEXT_PUBLIC_BACKEND_URL` (e.g. both `http://localhost:3000` and backend `http://localhost:8000`).

---

## 4. Quick reference

| Goal                         | Action |
|-----------------------------|--------|
| Use the app in the browser  | Open http://localhost:3000, then Dashboard, interaction form, or **/reagent**. |
| Check interaction for 2 drugs | Home → type two substances → “Check interaction”. |
| See substance profiles      | Dashboard link or http://localhost:3000/dashboard. |
| Populate interactions      | Run `python scripts/load_tripsit_to_neo4j.py` (Neo4j + .env required). |
| Populate substances        | Run `python scripts/sync_substances_to_core_api.py` (default list) or `... --all-tripsit` (every TripSit substance). |
| Refresh all integrated data| Run `python scripts/refresh_data.py`. |
| Test backend health        | GET http://localhost:8000/health. |
| Test core-api health       | GET http://localhost:8080/actuator/health. |
| Test both GET endpoints    | Run `python scripts/test_api_gets.py`. |
| Reagent test (LLM)         | `/reagent` with `OPENAI_API_KEY`; see §3.6. |
| Read LLM architecture      | This file, **§2b**. |
