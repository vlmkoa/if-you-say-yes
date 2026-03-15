#!/usr/bin/env python3
"""
Sync substance profiles (dosage from PsychonautWiki, adverse events from OpenFDA)
into core-api (PostgreSQL). The dashboard reads from PostgreSQL only — not from Neo4j.
Neo4j is only for the interaction checker (TripSit combos).

This script needs a list of substance names. You can provide it by:
  - default: small list (5 substances)
  - --from-psychonautwiki: fetch many names from PsychonautWiki API, then sync each (recommended for a large dashboard set)
  - --all-tripsit: use every substance in TripSit combos (same set as interaction data)
  - explicit names as arguments

Usage:
  python scripts/sync_substances_to_core_api.py                     # default list (5)
  python scripts/sync_substances_to_core_api.py --from-psychonautwiki  # many drugs from PsychonautWiki
  python scripts/sync_substances_to_core_api.py --all-tripsit        # every substance in TripSit combos
  python scripts/sync_substances_to_core_api.py caffeine aspirin     # explicit list

Requires: core-api running on CORE_API_URL (default http://localhost:8080).
"""

import argparse
import asyncio
import json
import os
import sys
from typing import Any, Dict, List, Set

import httpx

# Project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env from project root so CORE_API_URL is set when run as: python scripts/sync_substances_to_core_api.py
try:
    from dotenv import load_dotenv
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    load_dotenv(os.path.join(root, ".env"))
except ImportError:
    pass

from data_ingestion import OpenFDAIngestor, PsychonautWikiIngestor

CORE_API_URL = os.getenv("CORE_API_URL", "http://localhost:8080")
SYNC_ENDPOINT = f"{CORE_API_URL}/api/substances/sync"
TIMEOUT = 30.0
COMBOS_URL = "https://raw.githubusercontent.com/TripSit/drugs/main/combos.json"

# Example substance list when no args and no --all-tripsit
DEFAULT_SUBSTANCES = ["caffeine", "ibuprofen", "alcohol", "lsd", "mdma"]

# Known high addiction potential (0–10). Used to show RiskWarning on detail page when > 7.
# Keys are lowercased for lookup; add more as needed.
ADDICTION_POTENTIAL_OVERRIDE: Dict[str, float] = {
    "cocaine": 9,
    "heroin": 9,
    "methamphetamine": 9,
    "nicotine": 8,
    "alcohol": 7.5,
    "mdma": 6,
    "amphetamine": 8,
}


def all_substances_from_tripsit_combos(combos: Dict[str, Any]) -> List[str]:
    """Return sorted unique substance names from TripSit combos (top-level + all nested keys)."""
    names: Set[str] = set()
    for drug_a, interactions in combos.items():
        if not isinstance(interactions, dict):
            continue
        names.add(drug_a.strip())
        for drug_b in interactions.keys():
            if isinstance(drug_b, str):
                names.add(drug_b.strip())
    return sorted(n for n in names if n)


async def sync_one(
    client: httpx.AsyncClient,
    name: str,
    dosage_json: str | None,
    top_adverse_json: str | None,
    half_life: float | None = None,
    bioavailability: float | None = None,
    addiction_potential: float | None = None,
) -> bool:
    payload = {
        "name": name,
        "dosageJson": dosage_json,
        "topAdverseEventsJson": top_adverse_json,
        "halfLife": round(half_life, 2) if half_life is not None else None,
        "bioavailability": round(bioavailability, 2) if bioavailability is not None else None,
        "addictionPotential": round(addiction_potential, 1) if addiction_potential is not None else None,
    }
    r = await client.post(SYNC_ENDPOINT, json=payload, timeout=TIMEOUT)
    if r.status_code != 200:
        print(f"  {name}: sync failed {r.status_code} {r.text[:200]}")
        return False
    print(f"  {name}: synced")
    return True


async def fetch_tripsit_combos(client: httpx.AsyncClient) -> Dict[str, Any]:
    r = await client.get(COMBOS_URL, timeout=60.0)
    r.raise_for_status()
    return r.json()


async def main(substances: List[str]) -> None:
    pw = PsychonautWikiIngestor()
    openfda = OpenFDAIngestor()
    synced = 0
    async with httpx.AsyncClient() as client:
        for i, name in enumerate(substances, 1):
            dosage_json = None
            top_adverse_json = None
            half_life = None
            bioavailability = None
            try:
                pw_out = await pw.fetch_and_normalize(name)
                if "dosage_profile" in pw_out:
                    dosage_json = json.dumps(pw_out["dosage_profile"].model_dump())
                if pw_out.get("bioavailability") is not None:
                    bioavailability = float(pw_out["bioavailability"])
            except Exception as e:
                print(f"  [{i}/{len(substances)}] {name}: PsychonautWiki failed: {e}")
            try:
                fda_out = await openfda.fetch_and_normalize(name)
                if "top_adverse_events" in fda_out:
                    top_adverse_json = json.dumps(fda_out["top_adverse_events"])
            except Exception as e:
                print(f"  [{i}/{len(substances)}] {name}: OpenFDA failed: {e}")
            addiction = ADDICTION_POTENTIAL_OVERRIDE.get(name.strip().lower()) if name else None
            if await sync_one(
                client, name, dosage_json, top_adverse_json,
                half_life, bioavailability, addiction,
            ):
                synced += 1
    print(f"Synced {synced}/{len(substances)} substances to core-api.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync substance profiles (PsychonautWiki + OpenFDA) to core-api.")
    parser.add_argument(
        "--from-psychonautwiki",
        action="store_true",
        help="Fetch substance names from PsychonautWiki API, then sync each (many drugs; dashboard not tied to TripSit).",
    )
    parser.add_argument(
        "--all-tripsit",
        action="store_true",
        help="Sync every substance that appears in TripSit combos (same set as interaction data).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=500,
        metavar="N",
        help="Max substances when using --from-psychonautwiki (default 500).",
    )
    parser.add_argument(
        "substances",
        nargs="*",
        help="Substance names to sync. Ignored if --from-psychonautwiki or --all-tripsit is set.",
    )
    args = parser.parse_args()

    if args.from_psychonautwiki:
        async def resolve_pw():
            pw = PsychonautWikiIngestor()
            return await pw.fetch_all_substance_names(limit=args.limit)
        subs = asyncio.run(resolve_pw())
        print(f"Syncing {len(subs)} substances from PsychonautWiki (limit={args.limit})...")
    elif args.all_tripsit:
        async def resolve():
            async with httpx.AsyncClient() as client:
                combos = await fetch_tripsit_combos(client)
                return all_substances_from_tripsit_combos(combos)
        subs = asyncio.run(resolve())
        print(f"Syncing {len(subs)} substances from TripSit combos...")
    elif args.substances:
        subs = args.substances
    else:
        subs = DEFAULT_SUBSTANCES
        print(f"Using default list ({len(subs)} substances). Use --from-psychonautwiki or --all-tripsit for more.")

    asyncio.run(main(subs))
