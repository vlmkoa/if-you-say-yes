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

### Step 3: Create the graph schema in Neo4j

In Neo4j Browser (or cypher-shell), run Cypher that matches what the backend expects:

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

---

## 4. If something is not running

- **Containers:** `docker compose ps` — all should be “Up”.
- **Logs:** `docker compose logs frontend` or `docker compose logs backend` (or `core-api`, `postgres`).
- **Rebuild after code changes:** `docker compose up -d --build`.
