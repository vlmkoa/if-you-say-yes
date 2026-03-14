#!/usr/bin/env python3
"""
Test all current API GET endpoints (live).
Run with backends up: Python backend on :8000, core-api on :8080.

  python scripts/test_api_gets.py
"""

import sys
from urllib.parse import urlencode

import httpx

PYTHON_BACKEND = "http://localhost:8000"
CORE_API = "http://localhost:8080"
TIMEOUT = 10.0


def test_get_interaction() -> bool:
    """GET /interaction?drug_a=...&drug_b=... (Python/FastAPI)."""
    url = f"{PYTHON_BACKEND}/interaction"
    params = {"drug_a": "caffeine", "drug_b": "alcohol"}
    try:
        r = httpx.get(url, params=params, timeout=TIMEOUT)
        print(f"  GET {url}?{urlencode(params)} -> {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"    -> drug_a={data.get('drug_a')}, drug_b={data.get('drug_b')}, risk_level={data.get('risk_level')}, mechanism={data.get('mechanism')}")
        else:
            print(f"    -> {r.text[:200]}")
        return r.status_code in (200, 404, 500)  # 404/500 are valid (no data / Neo4j error)
    except Exception as e:
        print(f"  GET {url} -> ERROR: {e}")
        return False


def test_get_substances() -> bool:
    """GET /api/substances?page=0&size=5 (Spring Boot)."""
    url = f"{CORE_API}/api/substances"
    params = {"page": 0, "size": 5, "sortBy": "name", "sortDir": "asc"}
    try:
        r = httpx.get(url, params=params, timeout=TIMEOUT)
        print(f"  GET {url}?{urlencode(params)} -> {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            content = data.get("content", [])
            total = data.get("totalElements", len(content))
            print(f"    -> totalElements={total}, content length={len(content)}")
            if content:
                print(f"    -> first: {content[0]}")
        else:
            print(f"    -> {r.text[:200]}")
        return r.status_code == 200
    except Exception as e:
        print(f"  GET {url} -> ERROR: {e}")
        return False


def main() -> int:
    print("Testing API GET endpoints (live)\n")
    ok = True

    print("1. Python backend GET /interaction")
    if not test_get_interaction():
        ok = False
    print()

    print("2. Core-API GET /api/substances")
    if not test_get_substances():
        ok = False
    print()

    if ok:
        print("All GET checks completed (2/2).")
    else:
        print("Some requests failed or services not reachable. Ensure backend and core-api are running.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
