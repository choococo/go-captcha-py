"""Captcha answer stores — server-side caches for pending verifications.

The captcha answer (dots / block) must stay on the server: generate() hands
the images to the client while the answer is stored here under a key, then
verify() consumes it once.

Two ready-to-use implementations:
- MemoryStore: process-local dict + TTL eviction (single-worker deployments)
- Store protocol: implement your own on Redis etc. for distributed setups
"""

from __future__ import annotations

import hashlib
import secrets
import threading
import time
from typing import Any, Protocol


class Store(Protocol):
    """Storage protocol for pending captcha verifications."""

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        """Store an answer under key, expiring after ttl seconds (None = no expiry)."""
        ...

    def get(self, key: str) -> Any | None:
        """Fetch and keep the answer (None if missing/expired)."""
        ...

    def pop(self, key: str) -> Any | None:
        """Fetch and remove the answer (None if missing/expired)."""
        ...

    def delete(self, key: str) -> None:
        """Remove the answer."""
        ...


class MemoryStore:
    """Thread-safe in-memory store with TTL eviction.

    Suitable for single-process deployments; use a Redis-backed Store for
    multi-worker production setups.
    """

    def __init__(
        self, ttl: float = 600.0, default_ttl: float | None = None, sweep_interval: float = 60.0
    ) -> None:
        self._data: dict[str, tuple[Any, float | None]] = {}
        self._lock = threading.Lock()
        self._default_ttl = default_ttl if default_ttl is not None else ttl
        self._sweep_interval = sweep_interval
        self._last_sweep = time.monotonic()

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        with self._lock:
            self._maybe_sweep()
            expire_at = (
                (time.monotonic() + ttl)
                if ttl is not None
                else ((time.monotonic() + self._default_ttl) if self._default_ttl else None)
            )
            self._data[key] = (value, expire_at)

    def get(self, key: str) -> Any | None:
        with self._lock:
            item = self._data.get(key)
            if item is None:
                return None
            value, expire_at = item
            if expire_at is not None and time.monotonic() > expire_at:
                del self._data[key]
                return None
            return value

    def pop(self, key: str) -> Any | None:
        with self._lock:
            item = self._data.pop(key, None)
            if item is None:
                return None
            value, expire_at = item
            if expire_at is not None and time.monotonic() > expire_at:
                return None
            return value

    def delete(self, key: str) -> None:
        with self._lock:
            self._data.pop(key, None)

    def _maybe_sweep(self) -> None:
        now = time.monotonic()
        if now - self._last_sweep < self._sweep_interval:
            return
        self._last_sweep = now
        expired = [k for k, (_v, exp) in self._data.items() if exp is not None and now > exp]
        for k in expired:
            del self._data[k]


def gen_key(seed: str | None = None) -> str:
    """Generate a captcha id key.

    With seed (e.g. an IP or session id) the key is a stable-but-unguessable
    digest; without one it is a random token — mirroring the key derivation
    in go-captcha-example.
    """
    if seed:
        digest = hashlib.sha256(f"{seed}:{secrets.token_hex(8)}".encode()).hexdigest()
        return digest[:40]
    return secrets.token_hex(20)


__all__ = ["MemoryStore", "Store", "gen_key"]
