#!/usr/bin/env python3
"""
Assign a category to every substance in Postgres (core-api) using research-based lookup
and optional LLM fallback. Uses data_ingestion.categories (explicit mapping + heuristics)
first; if still unknown and OPENAI_API_KEY is set, asks the LLM to classify into one of
the allowed categories; otherwise sets "Other".

Requires: CORE_API_URL (default http://localhost:8080).
Optional: OPENAI_API_KEY for LLM fallback when mapping/heuristics don't match.
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

from data_ingestion.categories import CATEGORIES, get_category

CORE_API_URL = os.getenv("CORE_API_URL", "http://localhost:8080")
OPENAI_API_KEY = (os.getenv("OPENAI_API_KEY") or "").strip()
PAGE_SIZE = 200
TIMEOUT = 30.0

CATEGORY_LIST = ", ".join(CATEGORIES)


def fetch_all_substances() -> list[dict]:
    """Paginate GET /api/substances; return list of { id, name, category }. Uses id for PATCH to avoid drug name in URL (403 from filters)."""
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
                    "id": s.get("id"),
                    "name": (s.get("name") or "").strip(),
                    "category": (s.get("category") or "").strip() or None,
                })
            if data.get("last", True) or len(content) < PAGE_SIZE:
                break
            page += 1
    return out


def classify_with_llm(name: str) -> str | None:
    """Return one of CATEGORIES for the substance name, or None on failure."""
    if not OPENAI_API_KEY or not name:
        return None
    try:
        from openai import OpenAI
    except ImportError:
        return None
    client = OpenAI(api_key=OPENAI_API_KEY)
    prompt = f'''Classify the substance "{name}" into exactly one of these categories: {CATEGORY_LIST}.
Reply with only that single word, nothing else.'''
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=32,
        )
        text = (resp.choices[0].message.content or "").strip()
        for c in CATEGORIES:
            if c.lower() == text.lower():
                return c
        if text.lower() == "other":
            return "Other"
        return None
    except Exception:
        return None


def main() -> None:
    substances = fetch_all_substances()
    if not substances:
        print("No substances from core-api.")
        return
    print(f"Fetched {len(substances)} substances. Assigning categories (mapping/heuristics first, then LLM if needed).")
    updated = 0
    with httpx.Client(timeout=TIMEOUT) as client:
        for s in substances:
            name = s["name"]
            current = s["category"]
            # Research-based: explicit mapping + heuristics
            category = get_category(name)
            if category is None and OPENAI_API_KEY:
                category = classify_with_llm(name)
            if category is None:
                category = "Other"
            if current == category:
                continue
            # PATCH by id so drug name is never in the URL (avoids 403 from WAF/filters)
            sid = s.get("id")
            if sid is None:
                print(f"  SKIP {name!r}: no id", file=sys.stderr)
                continue
            r = client.patch(
                f"{CORE_API_URL}/api/substances/{sid}",
                json={"category": category},
            )
            if r.status_code == 200:
                updated += 1
                print(f"  {name!r} -> {category}")
            else:
                print(f"  FAIL {name!r}: {r.status_code} {r.text[:200]}", file=sys.stderr)
    print(f"Done. Updated {updated} substance(s).")


if __name__ == "__main__":
    main()
