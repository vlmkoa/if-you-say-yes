"""PsychonautWiki API ingestor (GraphQL)."""

from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel, Field

from .backoff import with_backoff
from .base import DataIngestor, NormalizedResult

PSYCHONAUTWIKI_GRAPHQL_URL = "https://api.psychonautwiki.org"

SUBSTANCES_QUERY = """
query Substances($query: String!) {
  substances(query: $query) {
    name
    roas {
      name
      dose {
        threshold
        light { min, max }
        common { min, max }
        strong { min, max }
        heavy
      }
      duration {
        onset { min, max, units }
        comeup { min, max, units }
        peak { min, max, units }
        offset { min, max, units }
        total { min, max, units }
      }
    }
  }
}
"""


# --- Pydantic models for parsed response ---


class MinMaxRange(BaseModel):
    """Min/max range; duration phases may include units (e.g. minutes)."""

    min: Optional[float] = None
    max: Optional[float] = None
    units: Optional[str] = None


class DoseRanges(BaseModel):
    """Dose levels per route of administration."""

    threshold: Optional[MinMaxRange] = None
    light: Optional[MinMaxRange] = None
    common: Optional[MinMaxRange] = None
    strong: Optional[MinMaxRange] = None
    heavy: Optional[MinMaxRange] = None


class DurationRanges(BaseModel):
    """Duration phases (typically in minutes)."""

    onset: Optional[MinMaxRange] = None
    comeup: Optional[MinMaxRange] = None
    peak: Optional[MinMaxRange] = None
    offset: Optional[MinMaxRange] = None
    total: Optional[MinMaxRange] = None


class RouteDosageProfile(BaseModel):
    """One route of administration with dose and duration."""

    name: str = Field(..., description="Route name (e.g. Oral, Insufflated)")
    dose: Optional[DoseRanges] = None
    duration: Optional[DurationRanges] = None


class SubstanceDosageProfile(BaseModel):
    """Substance dosage profile: name and routes of administration with dose/duration."""

    name: str = Field(..., description="Substance name")
    roas: List[RouteDosageProfile] = Field(default_factory=list)


def _to_min_max(d: Any) -> Optional[MinMaxRange]:
    """Parse API value (scalar or { min, max [, units] }) to MinMaxRange."""
    if d is None:
        return None
    if isinstance(d, (int, float)):
        return MinMaxRange(min=float(d), max=float(d))
    if isinstance(d, dict):
        return MinMaxRange(
            min=d.get("min"),
            max=d.get("max"),
            units=d.get("units"),
        )
    return None


def _parse_roa(roa: Dict[str, Any]) -> RouteDosageProfile:
    """Map one raw ROA from the API to RouteDosageProfile."""
    dose_raw = roa.get("dose") or {}
    duration_raw = roa.get("duration") or {}

    dose = DoseRanges(
        threshold=_to_min_max(dose_raw.get("threshold")),
        light=_to_min_max(dose_raw.get("light")),
        common=_to_min_max(dose_raw.get("common")),
        strong=_to_min_max(dose_raw.get("strong")),
        heavy=_to_min_max(dose_raw.get("heavy")),
    )
    duration = DurationRanges(
        onset=_to_min_max(duration_raw.get("onset")),
        comeup=_to_min_max(duration_raw.get("comeup")),
        peak=_to_min_max(duration_raw.get("peak")),
        offset=_to_min_max(duration_raw.get("offset")),
        total=_to_min_max(duration_raw.get("total")),
    )
    return RouteDosageProfile(
        name=roa.get("name") or "Unknown",
        dose=dose,
        duration=duration,
    )


def _response_to_dosage_profile(raw: Dict[str, Any]) -> SubstanceDosageProfile:
    """Parse API substance object into SubstanceDosageProfile."""
    name = raw.get("name") or ""
    roas_raw = raw.get("roas") or []
    roas = [_parse_roa(r) for r in roas_raw if isinstance(r, dict)]
    return SubstanceDosageProfile(name=name, roas=roas)


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

        raw = substances[0]
        dosage_profile = _response_to_dosage_profile(raw)

        return {
            "source": self.source_name,
            "substance": raw.get("name") or substance,
            "dosage_profile": dosage_profile,
            "roas": raw.get("roas"),
            "raw": raw,
        }
