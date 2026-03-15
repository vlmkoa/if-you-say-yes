import os
from typing import Optional, Dict, Any

import httpx
from neo4j import GraphDatabase, Driver
from neo4j.exceptions import Neo4jError

# Resolve opioids/benzo to TripSit canonical names (must match load_tripsit_to_neo4j + combos.json)
TRIPSIT_OPIOIDS = "opioids"
TRIPSIT_BENZO = "benzodiazepines"


_driver: Optional[Driver] = None


def _get_env_var(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Required environment variable '{name}' is not set.")
    return value


def _uri_for_ssl(uri: str) -> str:
    """If NEO4J_TRUST_SELF_SIGNED is set, use +ssc scheme to accept self-signed certs (e.g. corporate proxy)."""
    if os.getenv("NEO4J_TRUST_SELF_SIGNED", "").strip().lower() in ("1", "true", "yes"):
        return uri.replace("neo4j+s://", "neo4j+ssc://").replace("bolt+s://", "bolt+ssc://")
    return uri


def get_driver() -> Driver:
    """
    Lazily create and return a Neo4j driver instance for an AuraDB database.
    Connection details are read from environment variables:

    - NEO4J_URI
    - NEO4J_USERNAME
    - NEO4J_PASSWORD
    - NEO4J_TRUST_SELF_SIGNED (optional): set to 1/true to use neo4j+ssc (accept self-signed certs)
    """
    global _driver
    if _driver is None:
        uri = _get_env_var("NEO4J_URI")
        uri = _uri_for_ssl(uri)
        user = _get_env_var("NEO4J_USERNAME")
        password = _get_env_var("NEO4J_PASSWORD")

        _driver = GraphDatabase.driver(uri, auth=(user, password))
    return _driver


def close_driver() -> None:
    """Close the shared Neo4j driver, if it exists."""
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None


def neo4j_available() -> bool:
    """
    Return True if Neo4j is reachable (credentials set and a simple query succeeds).
    Use for health checks; does not raise.
    """
    try:
        driver = get_driver()
        database = os.getenv("NEO4J_DATABASE") or "neo4j"
        with driver.session(database=database) as session:
            session.run("RETURN 1").consume()
        return True
    except Exception:
        return False


def _get_substance_properties(driver: Driver, name: str) -> Optional[Dict[str, Any]]:
    """Return { category, interaction_reference } for a substance node, or None if not found."""
    database = os.getenv("NEO4J_DATABASE") or "neo4j"
    cypher = """
    MATCH (n:Substance) WHERE toLower(n.name) = $name
    RETURN n.category AS category, n.interaction_reference AS interaction_reference
    LIMIT 1
    """
    with driver.session(database=database) as session:
        record = session.execute_read(
            lambda tx: tx.run(cypher, name=name.lower().strip()).single()
        )
    if record is None:
        return None
    cat = record.get("category")
    ref = record.get("interaction_reference")
    return {
        "category": str(cat).strip() if cat else None,
        "interaction_reference": str(ref).strip() if ref else None,
    }


def _fetch_substance_from_core_api(name: str) -> Optional[Dict[str, Any]]:
    """
    Fetch category and interactionReference from core-api (Postgres) by substance name.
    Used when Neo4j has no node or no category/ref so opioids/benzo and similar-drug fallback still work.
    """
    base = (os.getenv("CORE_API_URL") or "").strip()
    if not base:
        return None
    url = f"{base.rstrip('/')}/api/substances/by-name"
    try:
        with httpx.Client(timeout=5.0) as client:
            r = client.get(url, params={"name": name})
        if r.status_code != 200:
            return None
        data = r.json()
        cat = data.get("category")
        ref = data.get("interactionReference")
        return {
            "category": str(cat).strip() if cat else None,
            "interaction_reference": str(ref).strip() if ref else None,
        }
    except Exception:
        return None


def _resolve_lookup_name(name: str, category: Optional[str]) -> str:
    """If category is Opioids/Benzo return TripSit canonical name; else return name (lowercased)."""
    n = name.lower().strip()
    if category == "Opioids":
        return TRIPSIT_OPIOIDS
    if category == "Benzo":
        return TRIPSIT_BENZO
    return n


def get_interaction(drug_a: str, drug_b: str) -> Optional[Dict[str, Any]]:
    """
    Look for an [:INTERACTS_WITH] relationship between two Substance nodes.
    Callers should pass lowercased names (API layer normalizes before calling).
    Cypher uses toLower(a.name) so graph data can be any case.
    """
    driver = get_driver()

    cypher = """
    MATCH (a:Substance)-[r:INTERACTS_WITH]-(b:Substance)
    WHERE toLower(a.name) = $drug_a AND toLower(b.name) = $drug_b
    RETURN r.risk_level AS risk_level,
           r.mechanism  AS mechanism
    LIMIT 1
    """

    database = os.getenv("NEO4J_DATABASE") or "neo4j"
    try:
        with driver.session(database=database) as session:
            record = session.execute_read(
                lambda tx: tx.run(
                    cypher,
                    drug_a=drug_a,
                    drug_b=drug_b,
                ).single()
            )
    except Neo4jError as e:
        # Bubble up to the API layer so it can translate this into an HTTP error.
        raise e

    if record is None:
        return None

    return {
        "risk_level": record.get("risk_level"),
        "mechanism": record.get("mechanism"),
    }


def get_interaction_resolved(
    drug_a: str,
    drug_b: str,
) -> Optional[Dict[str, Any]]:
    """
    Resolve interaction with category and relative fallback.
    - Resolves Opioids/Benzo to TripSit canonical names.
    - If no direct edge, tries interaction_reference for A or B (same category, from TripSit).
    Returns dict with risk_level, mechanism, and optional inferred, reference_drug_a, reference_drug_b.
    Returns None only when no interaction and no usable relative.
    """
    driver = get_driver()
    a = drug_a.lower().strip()
    b = drug_b.lower().strip()
    if not a or not b:
        return None

    props_a = _get_substance_properties(driver, a)
    props_b = _get_substance_properties(driver, b)
    # Postgres fallback: get category/ref from core-api when Neo4j has no node or is missing them (e.g. node exists but interaction_reference was set later in Postgres)
    postgres_a = _fetch_substance_from_core_api(a) if (not props_a or not props_a.get("interaction_reference") or not props_a.get("category")) else None
    postgres_b = _fetch_substance_from_core_api(b) if (not props_b or not props_b.get("interaction_reference") or not props_b.get("category")) else None
    if postgres_a:
        pa = props_a or {}
        props_a = {"category": pa.get("category") or postgres_a.get("category"), "interaction_reference": pa.get("interaction_reference") or postgres_a.get("interaction_reference")}
    if postgres_b:
        pb = props_b or {}
        props_b = {"category": pb.get("category") or postgres_b.get("category"), "interaction_reference": pb.get("interaction_reference") or postgres_b.get("interaction_reference")}
    cat_a = props_a.get("category") if props_a else None
    cat_b = props_b.get("category") if props_b else None
    ref_a = props_a.get("interaction_reference") if props_a else None
    ref_b = props_b.get("interaction_reference") if props_b else None
    if ref_a and isinstance(ref_a, str):
        ref_a = ref_a.strip().lower() or None
    if ref_b and isinstance(ref_b, str):
        ref_b = ref_b.strip().lower() or None

    key_a = _resolve_lookup_name(a, cat_a)
    key_b = _resolve_lookup_name(b, cat_b)

    result = get_interaction(key_a, key_b)
    if result is not None:
        return {**result, "inferred": False}

    # Try relative A' -> B (A' must be same category as A; ref_a is from TripSit)
    if ref_a and ref_a != key_a:
        result = get_interaction(ref_a, key_b)
        if result is not None:
            return {
                **result,
                "inferred": True,
                "reference_drug_a": ref_a,
                "reference_drug_b": None,
            }

    # Try A -> B' (relative of B)
    if ref_b and ref_b != key_b:
        result = get_interaction(key_a, ref_b)
        if result is not None:
            return {
                **result,
                "inferred": True,
                "reference_drug_a": None,
                "reference_drug_b": ref_b,
            }

    return None

