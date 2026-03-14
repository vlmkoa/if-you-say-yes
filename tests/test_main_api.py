from typing import Any, Dict
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from neo4j.exceptions import Neo4jError

from backend.main import app


client = TestClient(app)


@patch("backend.main.get_interaction")
def test_interaction_success(get_interaction_mock: MagicMock) -> None:
    get_interaction_mock.return_value = {
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


@patch("backend.main.get_interaction")
def test_interaction_not_found(get_interaction_mock: MagicMock) -> None:
    get_interaction_mock.return_value = None

    response = client.get("/interaction", params={"drug_a": "A", "drug_b": "B"})

    assert response.status_code == 404
    assert response.json()["detail"] == "No interaction found for the specified substances."


@patch("backend.main.get_interaction")
def test_interaction_handles_neo4j_error(get_interaction_mock: MagicMock) -> None:
    get_interaction_mock.side_effect = Neo4jError("boom")

    response = client.get("/interaction", params={"drug_a": "A", "drug_b": "B"})

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to query interaction graph."

