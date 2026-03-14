"""PsychonautWiki API ingestor (GraphQL)."""

from typing import Any, Dict

import httpx

from .backoff import with_backoff
from .base import DataIngestor, NormalizedResult

PSYCHONAUTWIKI_GRAPHQL_URL = "https://api.psychonautwiki.org/"

SUBSTANCES_QUERY = """
query Substances($query: String!) {
  substances(query: $query) {
    name
    summary
    roas {
      name
      dose { units, threshold { min, max }, heavy { min, max }, common { min, max }, light { min, max } }
      duration { afterglow { min, max }, comeup { min, max }, duration { min, max }, offset { min, max }, onset { min, max }, peak { min, max }, total { min, max } }
      bioavailability { min, max }
    }
  }
}
"""


class PsychonautWikiIngestor(DataIngestor):
    """Fetches substance data from PsychonautWiki GraphQL API."""

    @property
    def source_name(self) -> str:
        return "PsychonautWiki"

    async def fetch_and_normalize(self, substance: str) -> NormalizedResult:
        payload: Dict[str, Any] = {
            "query": SUBSTANCES_QUERY,
            "variables": {"query": substance},
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await with_backoff(
                client.post,
                PSYCHONAUTWIKI_GRAPHQL_URL,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        if "errors" in data:
            raise ValueError(f"GraphQL errors: {data['errors']}")

        substances = data.get("data", {}).get("substances") or []
        if not substances:
            raise ValueError(f"No substance found for: {substance}")

        # Use first match; normalize to common shape
        raw = substances[0]
        return {
            "source": self.source_name,
            "substance": raw.get("name") or substance,
            "summary": raw.get("summary"),
            "roas": raw.get("roas"),
            "raw": raw,
        }
