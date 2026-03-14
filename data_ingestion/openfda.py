"""OpenFDA Drug Label API ingestor."""

from typing import Any, Dict

import httpx

from .backoff import with_backoff
from .base import DataIngestor, NormalizedResult

OPENFDA_LABEL_URL = "https://api.fda.gov/drug/label.json"


class OpenFDAIngestor(DataIngestor):
    """Fetches drug label data from OpenFDA."""

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
        params: Dict[str, str | int] = {
            "search": f'openfda.brand_name:"{substance}"',
            "limit": 5,
        }
        if self._api_key:
            params["api_key"] = self._api_key

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await with_backoff(
                client.get,
                OPENFDA_LABEL_URL,
                params=params,
            )
            response.raise_for_status()
            data = response.json()

        results = data.get("results")
        if not results:
            # Fallback: search generic name
            params["search"] = f'openfda.generic_name:"{substance}"'
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await with_backoff(client.get, OPENFDA_LABEL_URL, params=params)
                response.raise_for_status()
                data = response.json()
            results = data.get("results")

        if not results:
            raise ValueError(f"No OpenFDA label found for: {substance}")

        # Normalize first result
        first = results[0]
        openfda = first.get("openfda") or {}
        brand = (openfda.get("brand_name") or [substance])[0]
        return {
            "source": self.source_name,
            "substance": brand,
            "indications": first.get("indications_and_usage"),
            "warnings": first.get("warnings"),
            "drug_interactions": first.get("drug_interactions"),
            "openfda": openfda,
            "raw": first,
        }
