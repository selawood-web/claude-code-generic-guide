"""Shared httpx client factory with sane timeouts and bounded retries."""

from __future__ import annotations

import time
from collections.abc import Callable

import httpx

DEFAULT_TIMEOUT = httpx.Timeout(connect=20.0, read=300.0, write=300.0, pool=20.0)


def client(**kwargs: object) -> httpx.Client:
    return httpx.Client(timeout=DEFAULT_TIMEOUT, follow_redirects=True, **kwargs)  # type: ignore[arg-type]


def retry[T](fn: Callable[[], T], *, attempts: int = 4, base_delay: float = 2.0) -> T:
    """Retry on transport errors and 429/5xx with exponential backoff."""
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            return fn()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status == 429 or status >= 500:
                last = exc
            else:
                raise
        except httpx.TransportError as exc:
            last = exc
        time.sleep(base_delay * (2**attempt))
    if last is None:  # pragma: no cover - loop always sets it before falling through
        raise RuntimeError("retry exhausted without an error")
    raise last
