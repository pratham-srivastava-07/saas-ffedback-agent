"""Per-workspace rate limiting for the endpoints that cost money.

A token bucket held in process memory. **This is per-process**: run four
uvicorn workers and each workspace gets four times the configured allowance.
That is a real limitation, accepted deliberately rather than pulling in Redis
for a single-node deployment. Move the bucket to Redis before scaling out.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from fastapi import HTTPException


@dataclass
class _Bucket:
    tokens: float
    updated_at: float


@dataclass
class RateLimiter:
    capacity: int
    window_seconds: float
    _buckets: dict[str, _Bucket] = field(default_factory=dict)

    def _refill_rate(self) -> float:
        return self.capacity / self.window_seconds if self.window_seconds else 0.0

    def check(self, key: str) -> None:
        """Consume one token for ``key``, or raise 429."""
        if self.capacity <= 0:
            return

        now = time.monotonic()
        bucket = self._buckets.get(key)

        if bucket is None:
            self._buckets[key] = _Bucket(tokens=self.capacity - 1, updated_at=now)
            return

        elapsed = now - bucket.updated_at
        bucket.tokens = min(
            float(self.capacity), bucket.tokens + elapsed * self._refill_rate()
        )
        bucket.updated_at = now

        if bucket.tokens < 1.0:
            retry_after = max(1, int((1.0 - bucket.tokens) / self._refill_rate()))
            raise HTTPException(
                status_code=429,
                detail=(
                    f"Rate limit exceeded: {self.capacity} requests per "
                    f"{int(self.window_seconds)}s."
                ),
                headers={"Retry-After": str(retry_after)},
            )

        bucket.tokens -= 1.0

    def reset(self) -> None:
        self._buckets.clear()
