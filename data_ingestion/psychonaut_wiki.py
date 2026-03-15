"""PsychonautWiki API ingestor (GraphQL)."""

from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel, Field

from .backoff import with_backoff
from .base import DataIngestor, NormalizedResult

PSYCHONAUTWIKI_GRAPHQL_URL = "https://api.psychonautwiki.org"

# List substance names only (for --from-psychonautwiki sync). Empty query + limit returns many.
SUBSTANCES_NAMES_QUERY = """
query Substances($query: String!, $limit: Int) {
  substances(query: $query, limit: $limit) {
    name
  }
}
"""

SUBSTANCES_QUERY = """
query Substances($query: String!) {
  substances(query: $query) {
    name
    roas {
      name
      bioavailability { min max }
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
        roas_raw = raw.get("roas") or []
        # Use first ROA's bioavailability (often oral) as a single percentage for the dashboard
        bioavailability_pct = None
        for roa in roas_raw:
            if not isinstance(roa, dict):
                continue
            bio = roa.get("bioavailability")
            if isinstance(bio, dict):
                mn, mx = bio.get("min"), bio.get("max")
                if mn is not None or mx is not None:
                    try:
                        bioavailability_pct = float(mn if mx is None else mx if mn is None else (float(mn) + float(mx)) / 2)
                        break
                    except (TypeError, ValueError):
                        pass

        return {
            "source": self.source_name,
            "substance": raw.get("name") or substance,
            "dosage_profile": dosage_profile,
            "roas": roas_raw,
            "raw": raw,
            "bioavailability": bioavailability_pct,
        }

    async def fetch_all_substance_names(self, limit: int = 1000) -> List[str]:
        """
        Fetch up to `limit` substance names from PsychonautWiki (broad query).
        Use for syncing "all" PW substances to the dashboard without TripSit.
        """
        payload: Dict[str, Any] = {
            "query": SUBSTANCES_NAMES_QUERY,
            "variables": {"query": "", "limit": limit},
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
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
        return [s.get("name") for s in substances if isinstance(s, dict) and s.get("name")]
