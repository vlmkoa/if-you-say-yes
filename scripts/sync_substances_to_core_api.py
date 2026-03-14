#!/usr/bin/env python3
"""
Run PsychonautWiki and OpenFDA ingestors for a list of substances and sync
dosage + adverse events to core-api (PostgreSQL) via POST /api/substances/sync.

Requires: core-api running on CORE_API_URL (default http://localhost:8080).
"""

import asyncio
import json
import os
import sys
from typing import List

import httpx

# Project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_ingestion import OpenFDAIngestor, PsychonautWikiIngestor

CORE_API_URL = os.getenv("CORE_API_URL", "http://localhost:8080")
SYNC_ENDPOINT = f"{CORE_API_URL}/api/substances/sync"
TIMEOUT = 30.0

# Example substance list; replace or load from file
DEFAULT_SUBSTANCES = ["caffeine", "ibuprofen", "alcohol", "lsd", "mdma"]


async def sync_one(
    client: httpx.AsyncClient,
    name: str,
    dosage_json: str | None,
    top_adverse_json: str | None,
) -> bool:
    payload = {
        "name": name,
        "dosageJson": dosage_json,
        "topAdverseEventsJson": top_adverse_json,
    }
    r = await client.post(SYNC_ENDPOINT, json=payload, timeout=TIMEOUT)
    if r.status_code != 200:
        print(f"  {name}: sync failed {r.status_code} {r.text[:200]}")
        return False
    print(f"  {name}: synced")
    return True


async def main(substances: List[str]) -> None:
    pw = PsychonautWikiIngestor()
    openfda = OpenFDAIngestor()
    synced = 0
    async with httpx.AsyncClient() as client:
        for name in substances:
            dosage_json = None
            top_adverse_json = None
            try:
                out = await pw.fetch_and_normalize(name)
                if "dosage_profile" in out:
                    dosage_json = json.dumps(out["dosage_profile"].model_dump())
            except Exception as e:
                print(f"  {name}: PsychonautWiki failed: {e}")
            try:
                out = await openfda.fetch_and_normalize(name)
                if "top_adverse_events" in out:
                    top_adverse_json = json.dumps(out["top_adverse_events"])
            except Exception as e:
                print(f"  {name}: OpenFDA failed: {e}")
            if await sync_one(client, name, dosage_json, top_adverse_json):
                synced += 1
    print(f"Synced {synced}/{len(substances)} substances to core-api.")


if __name__ == "__main__":
    subs = sys.argv[1:] if len(sys.argv) > 1 else DEFAULT_SUBSTANCES
    asyncio.run(main(subs))
