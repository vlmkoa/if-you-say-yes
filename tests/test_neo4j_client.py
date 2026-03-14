from typing import Any, Dict, Optional
from unittest.mock import MagicMock, patch

import pytest
from neo4j.exceptions import Neo4jError

from backend import neo4j_client


@patch("backend.neo4j_client.GraphDatabase")
def test_get_interaction_returns_data(graph_db_mock: MagicMock) -> None:
    # Arrange
    mock_driver = MagicMock()
    mock_session = MagicMock()
    mock_record: Dict[str, Any] = {"risk_level": "Dangerous", "mechanism": "CYP3A4 inhibition"}

    graph_db_mock.driver.return_value = mock_driver
    mock_driver.session.return_value.__enter__.return_value = mock_session
    mock_tx = MagicMock()

    def execute_read_side_effect(fn, *args, **kwargs):
        return fn(mock_tx)

    mock_session.execute_read.side_effect = execute_read_side_effect

    mock_tx.run.return_value.single.return_value = mock_record

    # Act
    with patch.object(neo4j_client, "_driver", None):
        with patch.dict(
            "os.environ",
            {
                "NEO4J_URI": "neo4j+s://test",
                "NEO4J_USERNAME": "user",
                "NEO4J_PASSWORD": "pass",
            },
        ):
            result: Optional[Dict[str, Any]] = neo4j_client.get_interaction("A", "B")

    # Assert
    assert result is not None
    assert result["risk_level"] == "Dangerous"
    assert result["mechanism"] == "CYP3A4 inhibition"


@patch("backend.neo4j_client.GraphDatabase")
def test_get_interaction_returns_none_when_no_record(graph_db_mock: MagicMock) -> None:
    mock_driver = MagicMock()
    mock_session = MagicMock()

    graph_db_mock.driver.return_value = mock_driver
    mock_driver.session.return_value.__enter__.return_value = mock_session
    mock_tx = MagicMock()

    def execute_read_side_effect(fn, *args, **kwargs):
        return fn(mock_tx)

    mock_session.execute_read.side_effect = execute_read_side_effect

    mock_tx.run.return_value.single.return_value = None

    with patch.object(neo4j_client, "_driver", None):
        with patch.dict(
            "os.environ",
            {
                "NEO4J_URI": "neo4j+s://test",
                "NEO4J_USERNAME": "user",
                "NEO4J_PASSWORD": "pass",
            },
        ):
            result = neo4j_client.get_interaction("A", "B")

    assert result is None


@patch("backend.neo4j_client.GraphDatabase")
def test_get_interaction_raises_on_neo4j_error(graph_db_mock: MagicMock) -> None:
    mock_driver = MagicMock()
    mock_session = MagicMock()

    graph_db_mock.driver.return_value = mock_driver
    mock_driver.session.return_value.__enter__.return_value = mock_session

    mock_session.execute_read.side_effect = Neo4jError("boom")

    with patch.object(neo4j_client, "_driver", None):
        with patch.dict(
            "os.environ",
            {
                "NEO4J_URI": "neo4j+s://test",
                "NEO4J_USERNAME": "user",
                "NEO4J_PASSWORD": "pass",
            },
        ):
            with pytest.raises(Neo4jError):
                neo4j_client.get_interaction("A", "B")

