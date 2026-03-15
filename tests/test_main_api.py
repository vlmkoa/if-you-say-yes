from typing import Any, Dict
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from neo4j.exceptions import Neo4jError

from backend.main import app


client = TestClient(app)


@patch("backend.main.get_interaction_resolved")
def test_interaction_success(get_interaction_resolved_mock: MagicMock) -> None:
    get_interaction_resolved_mock.return_value = {
        "risk_level": "Dangerous",
        "mechanism": "CYP3A4 inhibition",
    }

    response = client.get("/interaction", params={"drug_a": "A", "drug_b": "B"})

    assert response.status_code == 200
    data: Dict[str, Any] = response.json()
    assert data["drug_a"] == "A"
    assert data["drug_b"] == "B"
    assert data["risk_level"] == "Dangerous"
    assert data["mechanism"] == "CYP3A4 inhibition"


def test_interaction_missing_param_validation() -> None:
    response = client.get("/interaction", params={"drug_a": "A"})
    assert response.status_code == 422  # FastAPI validation for missing required param


@patch("backend.main.get_interaction_resolved")
def test_interaction_not_found(get_interaction_resolved_mock: MagicMock) -> None:
    get_interaction_resolved_mock.return_value = None

    response = client.get("/interaction", params={"drug_a": "A", "drug_b": "B"})

    assert response.status_code == 200
    data = response.json()
    assert data.get("no_known_effect") is True
    assert data.get("risk_level") == "Unknown"


@patch("backend.main.get_interaction_resolved")
def test_interaction_handles_neo4j_error(get_interaction_resolved_mock: MagicMock) -> None:
    get_interaction_resolved_mock.side_effect = Neo4jError("boom")

    response = client.get("/interaction", params={"drug_a": "A", "drug_b": "B"})

    assert response.status_code == 503
    assert "unavailable" in response.json()["detail"].lower()


@patch("backend.main.neo4j_available")
def test_health_ok(neo4j_available_mock: MagicMock) -> None:
    neo4j_available_mock.return_value = True
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json().get("neo4j") == "available"


@patch("backend.main.neo4j_available")
def test_health_unavailable(neo4j_available_mock: MagicMock) -> None:
    neo4j_available_mock.return_value = False
    response = client.get("/health")
    assert response.status_code == 503

