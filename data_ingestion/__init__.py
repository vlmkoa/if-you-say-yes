"""
Data ingestion module using the Strategy pattern.
All ingestors use httpx for async I/O and exponential backoff for rate limiting.
"""

from .base import DataIngestor
from .psychonaut_wiki import PsychonautWikiIngestor
from .tripsit import TripSitIngestor
from .openfda import OpenFDAIngestor

__all__ = [
    "DataIngestor",
    "PsychonautWikiIngestor",
    "TripSitIngestor",
    "OpenFDAIngestor",
]
