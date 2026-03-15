#!/usr/bin/env python3
"""
Populate interaction_reference for Postgres substances that are not in TripSit.
Uses OpenAI to pick one same-category drug from the TripSit list so the interaction
API can suggest "may be similar to X and Y". Skips Opioids and Benzo (they use canonical lookup).

Requires: CORE_API_URL, OPENAI_API_KEY. Optional: NEO4J_* not needed (we only call core-api).
"""

import os
import sys
from typing import Any

try:
    from dotenv import load_dotenv
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    load_dotenv(os.path.join(root, ".env"))
except ImportError:
    pass

import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CORE_API_URL = os.getenv("CORE_API_URL", "http://localhost:8080")
OPENAI_API_KEY = (os.getenv("OPENAI_API_KEY") or "").strip()
COMBOS_URL = "https://raw.githubusercontent.com/TripSit/drugs/main/combos.json"
PAGE_SIZE = 200
TIMEOUT = 30.0


def tripsit_names(combos: dict[str, Any]) -> set[str]:
    out = set()
    for drug_a, interactions in combos.items():
        if isinstance(interactions, dict):
            out.add(drug_a.strip().lower())
            for drug_b in interactions:
                if isinstance(drug_b, str):
                    out.add(drug_b.strip().lower())
    return out


def fetch_all_substances() -> list[dict]:
    """Return list of { id, name, category } for substances. Uses id for PATCH to avoid 403 from URL filters."""
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


def _normalize_llm_response(text: str) -> str:
    """Take first word/token from LLM response and normalize (lowercase, strip punctuation)."""
    if not text:
        return ""
    text = text.strip().lower()
    # Take first alphanumeric token (LLM might return "mdma." or "Answer: mdma")
    for part in text.replace(",", " ").replace(".", " ").split():
        clean = part.strip(".:;\"'")
        if clean and clean != "none":
            return clean
    return text.strip(".:;\"'") if text != "none" else ""


def ask_openai_for_reference(
    substance_name: str,
    category: str,
    tripsit_list: list[str],
    *,
    verbose: bool = False,
) -> str | None:
    """Return one drug from tripsit_list that is in the same category and might have similar interactions, or None."""
    if not OPENAI_API_KEY or not tripsit_list:
        return None
    cat = category or "Other"
    try:
        from openai import OpenAI
    except ImportError:
        if verbose:
            print(
                "  [skip] openai not installed. Install with: pip install openai\n"
                "  Or run inside the sync container: docker compose run --rm -e OPENAI_API_KEY=your_key sync python scripts/populate_interaction_references.py",
                file=sys.stderr,
            )
        return None
    client = OpenAI(api_key=OPENAI_API_KEY)
    # Send more names so LLM can pick; cap total prompt size
    names_sample = sorted(tripsit_list)[:400]
    prompt = f"""Given the substance "{substance_name}" (category: {cat}), choose exactly ONE substance from the list below that is most likely to have similar drug interactions. Reply with only that single word from the list, nothing else. If unsure, pick the closest by drug class.

List: {", ".join(names_sample)}"""
    try:
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,
        )
        raw = (r.choices[0].message.content or "").strip()
        text = _normalize_llm_response(raw)
        if not text or text == "none":
            if verbose:
                print(f"  [skip] {substance_name!r}: LLM returned empty or 'none'", file=sys.stderr)
            return None
        if text in tripsit_list:
            return text
        for t in tripsit_list:
            if t in text or text in t:
                return t
        if verbose:
            print(f"  [skip] {substance_name!r}: LLM said {raw!r} -> not in TripSit list", file=sys.stderr)
        return None
    except Exception as e:
        if verbose:
            print(f"  [error] {substance_name!r}: {e}", file=sys.stderr)
        return None


def main() -> None:
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    if not OPENAI_API_KEY:
        print("Set OPENAI_API_KEY", file=sys.stderr)
        sys.exit(1)
    try:
        from openai import OpenAI  # noqa: F401
    except ImportError:
        print(
            "This script needs the 'openai' package.\n"
            "  Option A (local):  pip install openai\n"
            "  Option B (Docker): docker compose run --rm -e OPENAI_API_KEY=$OPENAI_API_KEY sync python scripts/populate_interaction_references.py",
            file=sys.stderr,
        )
        sys.exit(1)
    combos = httpx.get(COMBOS_URL, timeout=60.0).json()
    tripsit = tripsit_names(combos)
    substances = fetch_all_substances()
    to_process = [
        s for s in substances
        if s["name"] and s["name"].lower() not in tripsit
        and s.get("category") not in ("Opioids", "Benzo")
    ]
    tripsit_list = list(tripsit)
    print(f"TripSit list has {len(tripsit_list)} names; {len(to_process)} substances to process.")
    updated = 0
    no_ref_count = 0
    patch_fail_count = 0
    with httpx.Client(timeout=TIMEOUT) as client:
        for i, s in enumerate(to_process):
            sid = s.get("id")
            if sid is None:
                continue
            use_verbose = verbose or i < 3  # first 3 always verbose to diagnose
            ref = ask_openai_for_reference(
                s["name"], s.get("category") or "Other", tripsit_list, verbose=use_verbose
            )
            if not ref:
                no_ref_count += 1
                continue
            r = client.patch(
                f"{CORE_API_URL}/api/substances/{sid}",
                json={"interactionReference": ref},
            )
            if r.status_code == 200:
                updated += 1
                print(f"  {s['name']} -> {ref}")
            else:
                patch_fail_count += 1
                if use_verbose:
                    print(f"  [patch failed] {s['name']!r}: {r.status_code} {r.text[:150]}", file=sys.stderr)
    print(f"Updated interaction_reference for {updated}/{len(to_process)} substances.")
    if no_ref_count or patch_fail_count:
        print(f"  (no ref from LLM: {no_ref_count}, PATCH failed: {patch_fail_count})", file=sys.stderr)


if __name__ == "__main__":
    main()
