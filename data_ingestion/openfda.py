"""OpenFDA Drug Event API ingestor (adverse events by medicinal product)."""

from typing import Any, Dict, List

import httpx

from .backoff import with_backoff
from .base import DataIngestor, NormalizedResult

OPENFDA_EVENT_URL = "https://api.fda.gov/drug/event.json"

# Top N adverse reactions to extract from count results
TOP_ADVERSE_LIMIT = 5


def _top_adverse_events(results: List[Dict[str, Any]], limit: int = TOP_ADVERSE_LIMIT) -> List[Dict[str, Any]]:
    """
    Extract the top `limit` most frequent adverse events from OpenFDA count results.
    Each result has "term" and "count". Returns a list of standardized dicts.
    """
    if not results or not isinstance(results, list):
        return []
    # OpenFDA count results are typically sorted by count descending; take first `limit`
    standardized: List[Dict[str, Any]] = []
    for item in results[:limit]:
        if not isinstance(item, dict):
            continue
        term = item.get("term")
        count = item.get("count")
        if term is not None:
            standardized.append({
                "term": str(term),
                "count": int(count) if count is not None else 0,
            })
    return standardized


class OpenFDAIngestor(DataIngestor):
    """Fetches adverse event data from OpenFDA Drug Event API."""

    def __init__(self, api_key: str | None = None):
        """
        Args:
            api_key: Optional OpenFDA API key (recommended for higher rate limits).
        """
        self._api_key = api_key

    @property
    def source_name(self) -> str:
        return "OpenFDA"

    async def fetch_and_normalize(self, substance: str) -> NormalizedResult:
        # search=patient.drug.medicinalproduct:"{substance_name}"
        # count=patient.reaction.reactionmeddrapt.exact → aggregated frequency of adverse reactions
        params: Dict[str, str | int] = {
            "search": f'patient.drug.medicinalproduct:"{substance}"',
            "count": "patient.reaction.reactionmeddrapt.exact",
        }
        if self._api_key:
            params["api_key"] = self._api_key

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await with_backoff(
                client.get,
                OPENFDA_EVENT_URL,
                params=params,
            )
            response.raise_for_status()
            data = response.json()

        results = data.get("results")
        if not results:
            raise ValueError(f"No OpenFDA adverse event data found for: {substance}")

        top_5 = _top_adverse_events(results, limit=TOP_ADVERSE_LIMIT)

        # Standardized Python dict: top adverse events + common normalized shape
        return {
            "source": self.source_name,
            "substance": substance,
            "top_adverse_events": top_5,
            "adverse_reactions": top_5,  # alias for clarity
            "raw_results": results,
        }
