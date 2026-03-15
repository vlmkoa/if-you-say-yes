#!/usr/bin/env python3
"""
Curl-like checks for the Python backend (Neo4j). Run with backend on :8000.
Use this to verify the backend and Neo4j from the host (e.g. after docker compose up).
"""

import sys
import urllib.request
import urllib.error
import json

BACKEND = "http://localhost:8000"
TIMEOUT = 10


def get(url: str) -> tuple[int, str]:
    """GET url; return (status_code, body_or_error)."""
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, (e.read().decode() if e.fp else str(e))
    except Exception as e:
        return -1, str(e)


def main() -> int:
    print("Backend checks (Python/Neo4j on :8000)\n")

    # 1. Health
    status, body = get(f"{BACKEND}/health")
    print(f"1. GET {BACKEND}/health")
    print(f"   Status: {status}")
    if status == 200:
        try:
            d = json.loads(body)
            print(f"   Body:   {d}")
            print(f"   -> Neo4j is reachable from the backend.")
        except Exception:
            print(f"   Body:   {body[:200]}")
    else:
        print(f"   Body:   {body[:300]}")
        print(f"   -> Neo4j is NOT reachable or backend env is missing (NEO4J_URI, etc.).")
    print()

    # 2. Interaction
    url = f"{BACKEND}/interaction?drug_a=caffeine&drug_b=alcohol"
    status, body = get(url)
    print(f"2. GET {BACKEND}/interaction?drug_a=caffeine&drug_b=alcohol")
    print(f"   Status: {status}")
    if status == 200:
        try:
            d = json.loads(body)
            print(f"   Body:   {d}")
            print(f"   -> Interaction lookup works.")
        except Exception:
            print(f"   Body:   {body[:200]}")
    elif status == 404:
        print(f"   Body:   {body[:200]}")
        print(f"   -> Backend is up; no interaction data in Neo4j for this pair (run load_tripsit_to_neo4j.py).")
    elif status == 503:
        print(f"   Body:   {body[:200]}")
        print(f"   -> Backend is up but Neo4j is unreachable (see .env and Neo4j).")
    else:
        print(f"   Body:   {body[:300]}")
    print()

    if status == 200 or status == 404:
        print("Backend is working. If the frontend still shows 'unavailable', the browser cannot reach the backend (CORS or wrong URL).")
    else:
        print("Backend or Neo4j is not OK. Check .env (NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD) and that Neo4j is running.")
    return 0 if status in (200, 404, 503) else 1


if __name__ == "__main__":
    sys.exit(main())
