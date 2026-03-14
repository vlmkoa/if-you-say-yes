"""Abstract base class for data ingestors (Strategy pattern)."""

from abc import ABC, abstractmethod
from typing import Any, Dict

# Normalized shape returned by all ingestors
NormalizedResult = Dict[str, Any]


class DataIngestor(ABC):
    """
    Abstract base class for substance data ingestors.
    Implementations fetch from a specific source and normalize to a common structure.
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Human-readable name of the data source (e.g. 'PsychonautWiki')."""
        ...

    @abstractmethod
    async def fetch_and_normalize(self, substance: str) -> NormalizedResult:
        """
        Fetch data for the given substance from the backing API/source
        and return a normalized result.

        Args:
            substance: Substance name or identifier to look up.

        Returns:
            A dict with at least: source, substance, raw or normalized fields.
            Implementations may add source-specific keys.

        Raises:
            httpx.HTTPError: On request failure after retries.
            ValueError: If the substance is not found or data is invalid.
        """
        ...
