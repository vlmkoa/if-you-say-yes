#!/usr/bin/env python3
"""
Standalone async script to fetch the TripSit interaction matrix and output
Cypher query strings to create INTERACTS_WITH relationships in Neo4j.

Usage:
    python scripts/fetch_tripsit_interactions.py

Fetches combos.json from TripSit/drugs (the interaction matrix), iterates
each substance's interactions, and prints one Cypher template plus
parameter sets for each interaction (or the query per interaction).
"""

import asyncio
import json
from typing import Any, Dict, Iterator, Tuple

import httpx

COMBOS_URL = "https://raw.githubusercontent.com/TripSit/drugs/main/combos.json"

CYPHER_TEMPLATE = (
    "MERGE (a:Substance {name: $drug_a}) "
    "MERGE (b:Substance {name: $drug_b}) "
    "MERGE (a)-[:INTERACTS_WITH {status: $status}]->(b)"
)


def parse_interactions(combos: Dict[str, Any]) -> Iterator[Tuple[str, str, str]]:
    """
    Iterate through the interactions for every substance in the TripSit combos payload.

    combos.json structure: { "<substance_a>": { "<substance_b>": { "status": "...", ... }, ... }, ... }
    Yields (drug_a, drug_b, status) for each interaction.
    """
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
    """Fetch and parse combos.json from TripSit."""
    response = await client.get(COMBOS_URL)
    response.raise_for_status()
    return response.json()


def cypher_and_params(combos: Dict[str, Any]) -> Iterator[Tuple[str, Dict[str, str]]]:
    """
    For each interaction, yield the Cypher query string and a params dict.
    Same query string every time; params are drug_a, drug_b, status.
    """
    for drug_a, drug_b, status in parse_interactions(combos):
        params = {"drug_a": drug_a, "drug_b": drug_b, "status": status}
        yield CYPHER_TEMPLATE, params


async def main() -> None:
    async with httpx.AsyncClient(timeout=60.0) as client:
        combos = await fetch_combos(client)

    print("# Cypher template (run with parameters below)")
    print(CYPHER_TEMPLATE)
    print()

    count = 0
    for cypher, params in cypher_and_params(combos):
        print("# params:", params)
        print(cypher)
        print()
        count += 1

    print(f"# Total interactions: {count}")


if __name__ == "__main__":
    asyncio.run(main())
