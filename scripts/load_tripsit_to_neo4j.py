#!/usr/bin/env python3
"""
Load TripSit interaction matrix into Neo4j.
Fetches combos.json, then runs MERGE for each interaction so that
GET /interaction (Python backend) can read risk_level and mechanism.

Requires: NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD in env (e.g. .env).
"""

import asyncio
import os
import sys

# Load .env from project root so NEO4J_* are set when run as: python scripts/load_tripsit_to_neo4j.py
try:
    from dotenv import load_dotenv
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    load_dotenv(os.path.join(root, ".env"))
except ImportError:
    pass
from typing import Any, Dict, Iterator, Tuple

import httpx

# Add project root for backend neo4j driver
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

COMBOS_URL = "https://raw.githubusercontent.com/TripSit/drugs/main/combos.json"

# Match backend neo4j_client: relationship has risk_level and mechanism
CYPHER = """
MERGE (a:Substance {name: $drug_a})
MERGE (b:Substance {name: $drug_b})
MERGE (a)-[r:INTERACTS_WITH]->(b)
SET r.risk_level = $risk_level, r.mechanism = $mechanism
"""


def parse_interactions(combos: Dict[str, Any]) -> Iterator[Tuple[str, str, str]]:
    """Yield (drug_a, drug_b, status) for each interaction."""
    for drug_a, interactions in combos.items():
        if not isinstance(interactions, dict):
            continue
        for drug_b, data in interactions.items():
            if not isinstance(data, dict):
                continue
            status = data.get("status")
            if status is None or not isinstance(status, str):
                status = "Unknown"
            yield (drug_a, drug_b, status)


async def fetch_combos(client: httpx.AsyncClient) -> Dict[str, Any]:
    r = await client.get(COMBOS_URL, timeout=60.0)
    r.raise_for_status()
    return r.json()


def _uri_for_ssl(uri: str) -> str:
    """If NEO4J_TRUST_SELF_SIGNED is set, use +ssc scheme to accept self-signed certs (e.g. corporate proxy)."""
    if os.getenv("NEO4J_TRUST_SELF_SIGNED", "").strip().lower() in ("1", "true", "yes"):
        return uri.replace("neo4j+s://", "neo4j+ssc://").replace("bolt+s://", "bolt+ssc://")
    return uri


def main_sync(combos: Dict[str, Any]) -> None:
    import neo4j
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    if not all((uri, user, password)):
        print("Set NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD", file=sys.stderr)
        sys.exit(1)
    database = os.getenv("NEO4J_DATABASE") or "neo4j"
    uri = _uri_for_ssl(uri)

    with neo4j.GraphDatabase.driver(uri, auth=(user, password)) as driver:
        with driver.session(database=database) as session:
            count = 0
            for drug_a, drug_b, status in parse_interactions(combos):
                # Lowercase so Postgres→Neo4j sync can MERGE on same key and interaction lookup is case-insensitive
                session.run(
                    CYPHER,
                    drug_a=drug_a.lower(),
                    drug_b=drug_b.lower(),
                    risk_level=status,
                    mechanism="",  # TripSit doesn't provide mechanism
                )
                count += 1
                if count % 100 == 0:
                    print(f"  {count} interactions written ...")
            print(f"Done. Total interactions: {count}")


async def main() -> None:
    async with httpx.AsyncClient() as client:
        combos = await fetch_combos(client)
    main_sync(combos)


if __name__ == "__main__":
    asyncio.run(main())
