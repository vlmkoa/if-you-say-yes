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

Replace with your real values. Then restart the backend:

```powershell
docker compose up -d backend
```

Docker Compose reads `.env` and passes these into the backend container.

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

To populate substance profiles with dosage (PsychonautWiki) and top adverse events (OpenFDA), run the sync script with **core-api** up (e.g. `docker compose up -d core-api` or full stack):

```powershell
python scripts/sync_substances_to_core_api.py
```

This uses the default substance list (`caffeine`, `ibuprofen`, `alcohol`, `lsd`, `mdma`). To sync specific substances:

```powershell
python scripts/sync_substances_to_core_api.py caffeine paracetamol
```

The script calls PsychonautWiki and OpenFDA ingestors, then **POST /api/substances/sync** to create or update profiles (including `dosageJson` and `topAdverseEventsJson`). **GET /api/substances** will then return these profiles with the new fields.

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

**Interaction form behind Nginx:** The form must call the backend via Nginx so the request is same-origin. Build the frontend with the backend base URL under Nginx:

```powershell
cd frontend
docker build --build-arg NEXT_PUBLIC_BACKEND_URL=http://localhost/api/backend -t ifyousayyes-frontend .
```

Or set `NEXT_PUBLIC_BACKEND_URL=http://localhost/api/backend` in your env before `npm run build`. Then the form will request `http://localhost/api/backend/health` and `http://localhost/api/backend/interaction` when you use the app at http://localhost.

**Without Nginx:** Use http://localhost:3000 (frontend), http://localhost:8000 (backend), http://localhost:8080 (core-api) as described in section 2. No build-arg change needed.
