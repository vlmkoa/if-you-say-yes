#!/usr/bin/env python3
"""
Sync all substance profiles from core-api (PostgreSQL) into Neo4j as nodes.
Each substance gets MERGED with name (lowercase), category, and interaction_reference.
Run after load_tripsit_to_neo4j.py so TripSit edges exist; this only adds/updates nodes
so the interaction API can resolve opioids/benzo and use interaction_reference for fallback.

Requires: CORE_API_URL (default http://localhost:8080), NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD.
"""

import os
import sys

try:
    from dotenv import load_dotenv
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    load_dotenv(os.path.join(root, ".env"))
except ImportError:
    pass

import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CORE_API_URL = os.getenv("CORE_API_URL", "http://localhost:8080")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")
PAGE_SIZE = 200
TIMEOUT = 30.0


def _uri_for_ssl(uri: str) -> str:
    if os.getenv("NEO4J_TRUST_SELF_SIGNED", "").strip().lower() in ("1", "true", "yes"):
        return uri.replace("neo4j+s://", "neo4j+ssc://").replace("bolt+s://", "bolt+ssc://")
    return uri


def fetch_all_substances() -> list[dict]:
    """Paginate GET /api/substances and return list of { name, category, interactionReference }. """
    out = []
    page = 0
    with httpx.Client(timeout=TIMEOUT) as client:
        while True:
            r = client.get(
                f"{CORE_API_URL}/api/substances",
                params={"page": page, "size": PAGE_SIZE, "sortBy": "id", "sortDir": "asc"},
            )
            r.raise_for_status()
            data = r.json()
            content = data.get("content", [])
            if not content:
                break
            for s in content:
                out.append({
                    "name": (s.get("name") or "").strip(),
                    "category": s.get("category"),
                    "interactionReference": s.get("interactionReference"),
                })
            if data.get("last", True) or len(content) < PAGE_SIZE:
                break
            page += 1
    return out


def main() -> None:
    if not all((NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)):
        print("Set NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD", file=sys.stderr)
        sys.exit(1)
    substances = fetch_all_substances()
    if not substances:
        print("No substances from core-api.")
        return
    uri = _uri_for_ssl(NEO4J_URI)
    import neo4j
    with neo4j.GraphDatabase.driver(uri, auth=(NEO4J_USERNAME, NEO4J_PASSWORD)) as driver:
        with driver.session(database=NEO4J_DATABASE) as session:
            cypher = """
            MERGE (n:Substance {name: $name})
            ON CREATE SET n.category = $category, n.interaction_reference = $ref
            ON MATCH SET n.category = $category, n.interaction_reference = $ref
            """
            for s in substances:
                name = (s["name"] or "").strip().lower()
                if not name:
                    continue
                session.run(
                    cypher,
                    name=name,
                    category=s.get("category") or "",
                    ref=s.get("interactionReference") or "",
                )
            print(f"Synced {len(substances)} substance nodes to Neo4j (category + interaction_reference).")


if __name__ == "__main__":
    main()
