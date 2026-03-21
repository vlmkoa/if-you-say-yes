# How to run and access the app

## 1. Start the stack (Docker)

From the project root:

```powershell
docker compose up -d --build
```

Wait until all containers are up (postgres, core-api, frontend, backend).

---

## 2. How to access it

| What | URL |
|------|-----|
| **Frontend (main UI)** | http://localhost:3000 |
| **Dashboard (substance profiles)** | http://localhost:3000/dashboard |
| **core-api (Phase 2 API)** | http://localhost:8080 — e.g. http://localhost:8080/api/substances?page=0&size=20 |
| **Python backend (Phase 1 API)** | http://localhost:8000 — Swagger: http://localhost:8000/docs |

- Use the **frontend** in the browser for the home page and the dashboard (grid of substances).
- The **drug interaction form** (Phase 1) must be placed on a page with `apiBaseUrl="http://localhost:8000"` so it calls the Python backend. If that page is not set up yet, you can still test the backend at http://localhost:8000/docs with `GET /interaction?drug_a=...&drug_b=...`.

### 2.1 Public demo (ngrok) — Docker frontend must rebuild

Next.js **bakes** `NEXT_PUBLIC_*` into the client JS at **build** time. For `docker compose`, set the URLs **browsers will use** (your machine’s `localhost` is wrong for remote users).

In the project root **`.env`** (same file as `NEO4J_*`), add:

```env
NEXT_PUBLIC_BACKEND_URL=https://your-backend.ngrok-free.dev
NEXT_PUBLIC_SPRING_API_URL=https://your-core-api.ngrok-free.dev
```

Then rebuild the frontend image so those values are compiled in:

```powershell
docker compose build --no-cache frontend
docker compose up -d frontend
```

If ngrok URLs change, update `.env` and run **`docker compose build --no-cache frontend`** again. For local-only use, omit these variables; compose defaults to `http://localhost:8000` and `http://localhost:8080`.

---

## 3. Making the backend (Neo4j) work correctly

The Python service (port 8000) needs a **Neo4j** database and the right schema, or `/interaction` will fail.

### Step 1: Get Neo4j

- **AuraDB (cloud):** https://neo4j.com/cloud/aura/ — create a free DB and copy the connection URI, username, and password.
- Or run **Neo4j locally** (e.g. Docker) and use `bolt://localhost:7687` with your user/password.

### Step 2: Give Docker the credentials

Create a file **`.env`** in the project root (same folder as `docker-compose.yml`):

```env
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
```

Replace with your real values. If you see **SSL certificate verify failed: self-signed certificate in certificate chain** (e.g. behind a corporate proxy or VPN that does TLS inspection), add:

```env
NEO4J_TRUST_SELF_SIGNED=1
```

This makes the driver use the `neo4j+ssc` scheme so the connection accepts the proxy’s certificate. Then restart the backend:

```powershell
docker compose up -d backend
```

Docker Compose reads `.env` and passes these into the backend container. The backend also uses **CORE_API_URL** (default `http://core-api:8080` in Docker) to look up **category** and **interaction_reference** from Postgres when a substance is missing in Neo4j or has no category/ref there—so opioids/benzo resolution and “similar drug” fallback still work in those cases. **Every drug in Postgres should still be synced to Neo4j as a node** (see section 5.3); the Postgres lookup is a fallback for resolution only.

### Step 3: Load interaction data into Neo4j (optional)

From the project root, with `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD` set (e.g. in `.env`), run:

```powershell
python scripts/load_tripsit_to_neo4j.py
```

This fetches TripSit’s combos.json and writes all interactions into Neo4j as `Substance` nodes and `INTERACTS_WITH` relationships (with `risk_level` and `mechanism`). After this, **GET /interaction** will return data for any pair present in TripSit.

Alternatively, create the graph manually in Neo4j Browser (or cypher-shell):

- **Nodes:** label `Substance`, property `name` (e.g. drug name).
- **Relationship:** `INTERACTS_WITH` between two `Substance` nodes, with properties `risk_level` and `mechanism`.

Example — create two substances and one interaction:

```cypher
CREATE (a:Substance {name: "Warfarin"}), (b:Substance {name: "Ibuprofen"})
CREATE (a)-[:INTERACTS_WITH {risk_level: "Caution", mechanism: "Increased bleeding risk"}]->(b);
```

### Step 4: Test the backend

- Open http://localhost:8000/docs and call **GET /interaction** with `drug_a=Warfarin` and `drug_b=Ibuprofen`. You should get a 200 with `risk_level` and `mechanism`.
- Or use the drug interaction form in the frontend (on a page that uses `apiBaseUrl="http://localhost:8000"`); it will call this endpoint and show the result.

### When Neo4j is not available

If Neo4j is off (e.g. AuraDB free instance sleeping, laptop closed, or local Neo4j stopped):

- **GET /interaction** returns **503** with a message that the interaction service is temporarily unavailable. The app does not crash.
- **GET /health** (http://localhost:8000/health) returns **503** when Neo4j is unreachable and **200** when it is reachable. The frontend can call this to show “Interaction check temporarily unavailable” instead of a generic error.
- Once Neo4j is back and reachable, the backend works again without restart (the next request will succeed).
- **Frontend:** The interaction form calls **GET /health** on load. If the backend is unavailable, it shows an amber banner (“Interaction check temporarily unavailable”) and disables the Check button. On 503 from **GET /interaction** it shows the same message.

### When PostgreSQL / core-api is not available

If PostgreSQL is down or core-api cannot reach it:

- **GET /api/substances** and **POST /api/substances/sync** may return 500 or 503. **GET /actuator/health** (http://localhost:8080/actuator/health) returns **503** when the app or DB is down, **200** when up.
- **Frontend:** The dashboard shows “Substance list temporarily unavailable. The database may be offline.” when the substances API returns 500 or 503.

---

## 4. If something is not running

- **Containers:** `docker compose ps` — all should be “Up”.
- **Logs:** `docker compose logs frontend` or `docker compose logs backend` (or `core-api`, `postgres`).
- **Rebuild after code changes:** `docker compose up -d --build`.

---

## 5. Syncing PsychonautWiki and OpenFDA into core-api (PostgreSQL)

To populate substance profiles with dosage (PsychonautWiki) and top adverse events (OpenFDA), run the sync script with **core-api** up (e.g. `docker compose up -d core-api` or full stack).

**Option A — local Python** (requires `pip install -r requirements.txt` or `python -m pip install httpx`):

```powershell
python scripts/sync_substances_to_core_api.py
```

**Option B — Docker** (dependencies are installed in the image at build time; no local Python env needed). First build: `docker compose build sync`. Then, with core-api running:

```powershell
docker compose run --rm sync python scripts/sync_substances_to_core_api.py --from-psychonautwiki
```

The **dashboard reads only from PostgreSQL** (core-api). Neo4j is only for the interaction checker. To get many drugs on the dashboard, sync using names from PsychonautWiki (recommended) or TripSit:

**Many drugs from PsychonautWiki (recommended; not tied to TripSit/Neo4j):**

```powershell
python scripts/sync_substances_to_core_api.py --from-psychonautwiki
```

This fetches up to 500 substance names from the PsychonautWiki API, then for each fetches dosage (PW) and adverse events (OpenFDA) and writes to core-api. Use `--limit 1000` for more.

**Every substance in TripSit combos (same set as interaction data):**

```powershell
python scripts/sync_substances_to_core_api.py --all-tripsit
```

The default list is small (5 substances). To sync only specific substances:

```powershell
python scripts/sync_substances_to_core_api.py caffeine paracetamol
```

The script calls PsychonautWiki and OpenFDA ingestors, then **POST /api/substances/sync** to create or update profiles (including `dosageJson`, `topAdverseEventsJson`, and optional `addictionPotential`). **GET /api/substances** will then return these profiles. Substances with `addictionPotential` > 7 show the Phase 3 risk warning modal on their detail page; the sync script sets this for a small set of known high-risk substances (e.g. cocaine, alcohol). Re-run sync to populate or update it.

**Why do some substances get "sync failed 403"?**  
The core-api itself does not return 403 for the sync endpoint (it permits `/api/**` and has no content blocklist). A **403 Forbidden** usually means something in front of the API is blocking the request:

- **Proxy, WAF, or content filter** (e.g. corporate or school network, or a cloud WAF) that inspects the request body and blocks payloads containing certain drug names (e.g. Alcohol, Cannabis, Cocaine, LSD, MDMA, Opioids). The script sends the substance name in the JSON body, so those requests can be blocked before they reach the app.
- **Different host or port**: If `CORE_API_URL` points at a server that applies such a filter, you’ll see 403 for those names.

**What to do:** Run the sync script against core-api with no proxy in between (e.g. `CORE_API_URL=http://localhost:8080` with core-api on the same machine). If you must go through a proxy, whitelist `POST /api/substances/sync` or disable body inspection for that URL. The script prints the first 300 characters of the response body on non-2xx so you can confirm the message (e.g. "Forbidden" or a WAF reason).

---

## 5.1 Dashboard search, sort, and community comments

- **Search:** Use the search bar on the dashboard; it filters by substance name (query param `q`). **Sort** dropdown: Name A–Z/Z–A, Half-life, Bioavailability.
- **Community comments:** On each substance’s detail page there is a **Community** section. Anyone can post anonymously (no login). Comments are stored as **PENDING** and only **approved** by a moderator are shown. To approve or reject, use the moderation API with a shared secret.

**Moderation API** (requires `X-Moderation-Key` header equal to `MODERATION_API_KEY` env):

- List pending: `GET /api/moderation/comments?page=0&size=20` with header `X-Moderation-Key: <your-key>`
- Approve: `PATCH /api/moderation/comments/{id}/approve` with same header
- Reject: `PATCH /api/moderation/comments/{id}/reject` with same header

Set `MODERATION_API_KEY` in the environment (or in `application.properties`) so moderators can call these endpoints (e.g. from a script or internal tool).

---

## 5.2 Phase 4: Reagent test analysis (vision LLM + chart)

The **Reagent test** page (http://localhost:3000/reagent) uploads a photo of a reagent reaction or chart. The Python backend uses **OpenAI GPT-4o (vision)** to extract **structured, observable** information from the image; **substance suggestions** come from a **local** color chart (`backend/reagent_chart_data.py`), not from the LLM naming drugs.

**For a deeper flow diagram and all other LLM uses in this repo** (maintenance scripts, models), see **`FLOW_AND_TEST.md` §2b**.

### What the LLM does vs what code does

| Step | Component | Role |
|------|-----------|------|
| 1 | **GPT-4o vision** (`backend/reagent_vision.py`) | Sees the image + optional user text; returns **JSON** with `colors[]` (each with `hex`, optional `method` / column), `labels[]` (visible text), optional `description`. Prompts tell the model **not** to identify an unknown sample as a specific drug. |
| 2 | **Resolver** (`resolve_reagent_for_color_entry`) | Picks the **reagent test** for each swatch: per-color `method` from vision → optional form field **`reagent`** → **`prompt`** text (e.g. “Marquis”, “Md”) → OCR `labels` if there is only one color. Supports chart initials (**M**→Marquis, **Md**→Mandelin, **Mr/Mo**→Morris, etc.). |
| 3 | **Chart** (`reagent_chart_data.py`) | For each `(hex, resolved_method)`, scores drugs **only in that reagent’s column**; each drug may have multiple reference hexes (e.g. purple→black). **No LLM** here — Euclidean distance in RGB and normalized scores. |

If the reagent type cannot be resolved, the API returns `needs_reagent: true` for that color so the user can choose the test from the dropdown or type it and upload again.

**Requirements:**

- **OPENAI_API_KEY** on the backend (e.g. root `.env`). Without it, **POST /reagent/analyze** returns **503**.
- Frontend uses **`NEXT_PUBLIC_BACKEND_URL`** (default `http://localhost:8000`) for `POST /reagent/analyze`.

**User flow:**

1. Open **Reagent test** in the nav; optionally set **Reagent test** dropdown and/or description (e.g. column letter or full name).
2. Upload **JPEG / PNG / WebP** (max 10 MB).
3. Frontend sends **multipart**: `image`, optional `prompt`, optional **`reagent`** (explicit override when the photo has no header).
4. UI shows each detected color, resolved **method** (if any), horizontal bar chart of **matches**, **`reference_note`** (DanceSafe / verify with kit), and the disclaimer: *“Colorimetric testing is presumptive and subject to contamination errors.”*

**API:** `POST /reagent/analyze` — multipart: `image` (file), `prompt` (optional), `reagent` (optional). Response includes `colors[]` (`hex`, `method`, `needs_reagent`, `matches[]`), `labels`, `known_reagents`, `reference_note`.

**Chart data:** `backend/reagent_chart_data.py` — hierarchical **method → substance → [hex, …]**; hex values are approximations; always compare to your **vendor / DanceSafe** chart.

---

## 5.3 Categories, Neo4j sync, and interaction fallback

**Dashboard (Postgres)** substances are categorized (Stimulant, Opioids, Benzo, Psychedelics, Dissociative, Alcohol, Cannabinoid, Depressant, SSRI, MAOI, Other) so the UI can show **Category** on each card. Categories come from a research-based mapping and heuristics in `data_ingestion/categories.py`; when syncing (e.g. `sync_substances_to_core_api.py --from-psychonautwiki`) only names in the mapping get a category. To **assign a category to every drug already in the DB**, run:
   ```powershell
   python scripts/assign_categories.py
   ```
   This uses the same mapping plus substring heuristics first; if a substance still has no category and `OPENAI_API_KEY` is set, it uses the LLM to classify into one of the categories; otherwise it sets "Other". Then re-run **Sync Postgres → Neo4j** (step 3) so Neo4j nodes get the new categories.

**Neo4j** holds TripSit interaction edges and, after sync, **all** Postgres substances as nodes (with `category` and `interaction_reference`). So the interaction checker can resolve by category and by “relative” drug.

**Order of operations:**

1. **Load TripSit into Neo4j** (creates nodes + edges; names are lowercased):
   ```powershell
   python scripts/load_tripsit_to_neo4j.py
   ```

2. **Sync substances to Postgres** (with category from mapping):
   ```powershell
   python scripts/sync_substances_to_core_api.py --from-psychonautwiki
   ```

3. **Sync Postgres → Neo4j** (MERGE every substance as a node with category and interaction_reference):
   ```powershell
   python scripts/sync_postgres_to_neo4j.py
   ```
   Requires core-api and Neo4j running; uses `CORE_API_URL` and `NEO4J_*`.

4. **Optional: backfill interaction_reference** ("most similar" drug for interaction fallback) for non–TripSit, non-opioid/benzo drugs (uses OpenAI to pick a same-category TripSit drug; writes to Postgres via PATCH by id to avoid 403):
   - **Local:** `pip install openai` then `python scripts/populate_interaction_references.py` (requires `OPENAI_API_KEY` in `.env`).
   - **Docker:** `docker compose run --rm -e OPENAI_API_KEY=$OPENAI_API_KEY sync python scripts/populate_interaction_references.py` (sync image has `openai`; core-api must be reachable as `core-api:8080`).
   Then re-run step 3 so Neo4j gets the new references. The dashboard and substance detail page show **Similar drug (for interactions)** when this is set.

**Interaction API behavior:**

- **Every Postgres drug is a Neo4j node:** All substances in Postgres are synced to Neo4j as nodes (step 3 in 5.3) so they exist in the graph and can be displayed and used consistently.
- **Opioids / Benzo:** For interaction checking, if a drug’s category is Opioids or Benzo (from Neo4j or, as fallback, from Postgres), the backend resolves it to the TripSit canonical name (`opioids` or `benzodiazepines`) for the Neo4j lookup. So e.g. “diazepam” + “alcohol” returns the same result as “benzodiazepines” + “alcohol”; no “similar drug” reference is needed for opioids/benzos.
- **Relative fallback:** If there is no direct edge for A–B, the backend tries A’–B or A–B’ where A’/B’ is the substance’s `interaction_reference` (from Neo4j or from Postgres). If found, the response is `inferred: true` and the UI shows: “Interaction data may be similar to [reference].”
- **No known effect:** If no edge and no usable relative, the API returns 200 with `no_known_effect: true` and `risk_level: "Unknown"`; the UI shows a gray “No known effects yet” box.

**Core-api endpoints:**

- `GET /api/substances/by-name?name=...` — fetch one profile by name.
- `PATCH /api/substances/by-name?name=...` — body may include `"category"` and/or `"interactionReference"` (used by `assign_categories.py` and `populate_interaction_references.py`).

### 5.4 Verify that the database has changed (and is it permanent?)

**Check Postgres (substances, category, interaction_reference):**

- **Via API:** With core-api running, open in a browser or use curl:
  ```powershell
  curl "http://localhost:8080/api/substances?page=0&size=5"
  ```
  In the JSON, look for `"category"` and `"interactionReference"` on each substance. If you ran `assign_categories.py`, many will have a category; if you ran `populate_interaction_references.py`, some will have `interactionReference`.
- **Via database:** If you use Docker Postgres:
  ```powershell
  docker compose exec postgres psql -U postgres -d ifyousayyes -c "SELECT COUNT(*) AS total, COUNT(category) AS with_category, COUNT(interaction_reference) AS with_ref FROM substance_profile;"
  ```
  You should see non-zero counts for `with_category` and optionally `with_ref` after running the scripts.

**Check Neo4j (interaction edges and substance nodes):**

- In **Neo4j Aura** (or Neo4j Browser), run:
  ```cypher
  MATCH (n:Substance) RETURN count(n) AS substance_nodes;
  MATCH ()-[r:INTERACTS_WITH]->() RETURN count(r) AS interaction_edges;
  ```
  After `load_tripsit_to_neo4j.py` you should have many `INTERACTS_WITH` edges; after `sync_postgres_to_neo4j.py` you should have more `Substance` nodes (and nodes will have `category` / `interaction_reference` if set in Postgres).

**Is it permanent?**

- **Yes.** Everything written by these scripts is stored in the databases (Postgres and Neo4j). You do **not** need to run the populate/sync scripts again unless you want to:
  - **Refresh** data (e.g. TripSit or PsychonautWiki added new entries), or
  - **Re-run** after restoring a blank database.
- So: run once (or when you add a new DB), then leave it. Re-run only when you intentionally refresh (see section 6).

---

## 6. Refresh protocol (keeping data up to date)

External sources (TripSit, PsychonautWiki, OpenFDA) change over time. To refresh integrated data:

**One-shot refresh (Neo4j + core-api):**

```powershell
python scripts/refresh_data.py
```

**Refresh only Neo4j or only core-api:**

```powershell
python scripts/refresh_data.py --neo4j
python scripts/refresh_data.py --core-api
```

**Suggested schedule:** run a full refresh weekly (e.g. Sunday night). On Windows you can use Task Scheduler; on Linux/macOS use cron, for example:

```cron
0 3 * * 0 cd /path/to/ifyousayyes && python scripts/refresh_data.py
```

Ensure Neo4j and core-api are running (or reachable) when the job runs. If Neo4j is down, the Neo4j step is skipped or fails; core-api sync can still run.

---

## 7. Optional: Nginx reverse proxy

Using Nginx gives a **single entry point** (port 80), can simplify deployment, and allows SSL termination and rate limiting later.

**When it helps:** One hostname/port for the app; the browser talks only to Nginx (same origin for the interaction form if you set the backend path under Nginx). Useful for production-like setups or when you don’t want to expose multiple ports.

**Run with Nginx:**

```powershell
docker compose --profile nginx up -d --build
```

Then open **http://localhost** (port 80). Nginx proxies:

- **/** → frontend (Next.js)
- **/api/backend/** → Python backend (e.g. `/api/backend/interaction`, `/api/backend/health`)

**Interaction form behind Nginx:** The form must call the backend via Nginx so the request is same-origin. Build the frontend with the backend base URL under Nginx (and core-api if proxied), e.g. in root `.env`:

```env
NEXT_PUBLIC_BACKEND_URL=http://localhost/api/backend
NEXT_PUBLIC_SPRING_API_URL=http://localhost/api/core
```

Then `docker compose build frontend` (or `cd frontend` and `docker build` with both `--build-arg` values). Or set the same vars before `npm run build`.

**Without Nginx:** Use http://localhost:3000 (frontend), http://localhost:8000 (backend), http://localhost:8080 (core-api) as described in section 2. Defaults need no extra build args.
