"""TripSit API ingestor."""

from typing import Any, Dict

import httpx

from .backoff import with_backoff
from .base import DataIngestor, NormalizedResult

TRIPSIT_DRUG_API_URL = "https://tripbot.tripsit.me/api/tripsit/getDrug"


class TripSitIngestor(DataIngestor):
    """Fetches substance/drug data from TripSit TripBot API."""

    @property
    def source_name(self) -> str:
        return "TripSit"

    async def fetch_and_normalize(self, substance: str) -> NormalizedResult:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await with_backoff(
                client.get,
                TRIPSIT_DRUG_API_URL,
                params={"name": substance},
            )
            response.raise_for_status()
            data = response.json()

        if not data or data.get("err") is True:
            raise ValueError(f"No drug data found for: {substance}")

        # TripBot returns { data: { ... } } or similar
        payload = data.get("data") if isinstance(data.get("data"), dict) else data
        if not payload:
            raise ValueError(f"No drug data found for: {substance}")

        return {
            "source": self.source_name,
            "substance": payload.get("name") or substance,
            "summary": payload.get("description") or payload.get("summary"),
            "effects": payload.get("effects"),
            "interactions": payload.get("interactions"),
            "raw": payload,
        }
