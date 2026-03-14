import os
from typing import Optional, Dict, Any

from neo4j import GraphDatabase, Driver
from neo4j.exceptions import Neo4jError


_driver: Optional[Driver] = None


def _get_env_var(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Required environment variable '{name}' is not set.")
    return value


def get_driver() -> Driver:
    """
    Lazily create and return a Neo4j driver instance for an AuraDB database.
    Connection details are read from environment variables:

    - NEO4J_URI
    - NEO4J_USERNAME
    - NEO4J_PASSWORD
    """
    global _driver
    if _driver is None:
        uri = _get_env_var("NEO4J_URI")
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


def get_interaction(drug_a: str, drug_b: str) -> Optional[Dict[str, Any]]:
    """
    Look for an [:INTERACTS_WITH] relationship between two Substance nodes.

    The Cypher query assumes a schema like:
      (a:Substance {name: $drug_a})-[:INTERACTS_WITH {risk_level, mechanism}]-(b:Substance {name: $drug_b})

    Returns a dict containing "risk_level" and "mechanism" if an interaction is found,
    otherwise returns None.
    """
    driver = get_driver()

    cypher = """
    MATCH (a:Substance {name: $drug_a})-[r:INTERACTS_WITH]-(b:Substance {name: $drug_b})
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

