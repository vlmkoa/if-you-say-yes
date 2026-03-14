"""Exponential backoff for rate limiting and transient failures."""

import asyncio
import logging
from typing import Callable, TypeVar

import httpx

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Default: max 5 retries, base delay 1s, max delay 60s
DEFAULT_MAX_RETRIES = 5
DEFAULT_BASE_DELAY = 1.0
DEFAULT_MAX_DELAY = 60.0


def _is_retryable(response: httpx.Response) -> bool:
    """Return True if the response suggests we should retry with backoff."""
    if response.status_code == 429:  # Too Many Requests
        return True
    if 500 <= response.status_code < 600:  # Server errors
        return True
    return False


async def with_backoff(
    request_fn: Callable[..., T],
    *args,
    max_retries: int = DEFAULT_MAX_RETRIES,
    base_delay: float = DEFAULT_BASE_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
    **kwargs,
) -> T:
    """
    Execute an async httpx request with exponential backoff on 429 and 5xx.
    Usage: await with_backoff(client.get, url) or await with_backoff(client.post, url, json=...).
    """
    last_exc = None
    for attempt in range(max_retries + 1):
        try:
            response = await request_fn(*args, **kwargs)
            if _is_retryable(response) and attempt < max_retries:
                delay = min(base_delay * (2 ** attempt), max_delay)
                logger.warning(
                    "Rate limit or server error (attempt %s/%s), retrying in %.1fs: %s",
                    attempt + 1,
                    max_retries + 1,
                    delay,
                    response.status_code,
                )
                await asyncio.sleep(delay)
                continue
            if _is_retryable(response):
                response.raise_for_status()
            return response  # type: ignore
        except httpx.HTTPStatusError as e:
            last_exc = e
            if e.response is not None and not _is_retryable(e.response):
                raise
            if attempt == max_retries:
                raise
            delay = min(base_delay * (2 ** attempt), max_delay)
            logger.warning(
                "Request failed (attempt %s/%s), retrying in %.1fs: %s",
                attempt + 1,
                max_retries + 1,
                delay,
                e,
            )
            await asyncio.sleep(delay)
        except (httpx.RequestError, httpx.TimeoutException) as e:
            last_exc = e
            if attempt == max_retries:
                raise
            delay = min(base_delay * (2 ** attempt), max_delay)
            logger.warning(
                "Request error (attempt %s/%s), retrying in %.1fs: %s",
                attempt + 1,
                max_retries + 1,
                delay,
                e,
            )
            await asyncio.sleep(delay)
    if last_exc is not None:
        raise last_exc
    raise RuntimeError("Unexpected exit from backoff loop")
