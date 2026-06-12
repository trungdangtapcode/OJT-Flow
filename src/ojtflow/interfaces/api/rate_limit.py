"""API rate limiting middleware helpers."""

from __future__ import annotations

import hashlib
import json
import threading
import time
from pathlib import Path
from typing import Protocol

from fastapi import Request
from fastapi.responses import JSONResponse

from ojtflow.config import Settings
from ojtflow.core.contracts.rate_limit import (
    RateLimitDecision,
    RateLimitPolicy,
    RateLimitRule,
)
from ojtflow.interfaces.api.responses import public_jsonable

try:
    import redis
    from redis.exceptions import RedisError
except ImportError:  # pragma: no cover
    redis = None

    class RedisError(Exception):
        pass


class RateLimitStore(Protocol):
    def increment(
        self,
        key: str,
        *,
        window_seconds: int,
        now: int,
    ) -> tuple[int, int]: ...


class InMemoryRateLimitStore:
    """Process-local fixed-window counter store."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[str, tuple[int, int]] = {}

    def increment(
        self,
        key: str,
        *,
        window_seconds: int,
        now: int,
    ) -> tuple[int, int]:
        window_start = now - (now % window_seconds)
        reset_at = window_start + window_seconds
        bucket_key = f"{key}:{window_start}"
        with self._lock:
            self._prune(now)
            current, _ = self._counters.get(bucket_key, (0, reset_at))
            current += 1
            self._counters[bucket_key] = (current, reset_at)
        return current, reset_at

    def _prune(self, now: int) -> None:
        expired = [key for key, (_, reset_at) in self._counters.items() if reset_at <= now]
        for key in expired:
            self._counters.pop(key, None)


class RedisRateLimitStore:
    """Redis fixed-window counter store."""

    def __init__(
        self,
        redis_url: str,
        *,
        prefix: str,
        fallback: RateLimitStore | None = None,
    ) -> None:
        if redis is None:
            raise RuntimeError("redis package is not installed")
        self.client = redis.from_url(redis_url, decode_responses=True)
        self.client.ping()
        self.prefix = prefix.strip(":") or "ojtflow:rate_limit"
        self.fallback = fallback

    def increment(
        self,
        key: str,
        *,
        window_seconds: int,
        now: int,
    ) -> tuple[int, int]:
        window_start = now - (now % window_seconds)
        reset_at = window_start + window_seconds
        redis_key = f"{self.prefix}:{key}:{window_start}"
        try:
            pipe = self.client.pipeline()
            pipe.incr(redis_key)
            pipe.expire(redis_key, window_seconds + 5)
            count, _ = pipe.execute()
            return int(count), reset_at
        except RedisError:
            if self.fallback is not None:
                return self.fallback.increment(
                    key,
                    window_seconds=window_seconds,
                    now=now,
                )
            raise


class RateLimiter:
    """Data-driven route-category rate limiter."""

    def __init__(self, *, policy: RateLimitPolicy, store: RateLimitStore) -> None:
        self.policy = policy
        self.store = store

    def check(self, request: Request, *, settings: Settings) -> RateLimitDecision | None:
        if not settings.rate_limit_enabled:
            return None
        path = request.url.path
        method = request.method.upper()
        rules = _matching_rules(self.policy, method=method, path=path)
        if not rules:
            return None
        now = int(time.time())
        most_restrictive: RateLimitDecision | None = None
        for rule in rules:
            identity = _request_identity(request, settings=settings, scope=rule.scope)
            key = _counter_key(rule, identity=identity)
            count, reset_at = self.store.increment(
                key,
                window_seconds=rule.window_seconds,
                now=now,
            )
            remaining = max(0, rule.limit - count)
            decision = RateLimitDecision(
                allowed=count <= rule.limit,
                rule_key=rule.key,
                limit=rule.limit,
                remaining=remaining,
                reset_seconds=max(1, reset_at - now),
                window_seconds=rule.window_seconds,
                scope=rule.scope,
            )
            if not decision.allowed:
                return decision
            if most_restrictive is None or decision.remaining < most_restrictive.remaining:
                most_restrictive = decision
        return most_restrictive


def load_rate_limit_policy(path: Path) -> RateLimitPolicy:
    """Load a rate-limit policy file."""

    raw = json.loads(path.read_text(encoding="utf-8"))
    return RateLimitPolicy.model_validate(raw)


def build_rate_limiter(settings: Settings) -> RateLimiter:
    """Build the configured rate limiter."""

    policy = load_rate_limit_policy(settings.resolved_rate_limit_policy_path)
    store: RateLimitStore
    if settings.rate_limit_backend == "redis":
        store = RedisRateLimitStore(
            settings.redis_url,
            prefix=settings.rate_limit_redis_prefix,
        )
    elif settings.rate_limit_backend == "auto" and settings.storage_backend == "postgres":
        fallback = InMemoryRateLimitStore()
        try:
            store = RedisRateLimitStore(
                settings.redis_url,
                prefix=settings.rate_limit_redis_prefix,
                fallback=fallback,
            )
        except (RedisError, RuntimeError, ValueError):
            store = fallback
    else:
        store = InMemoryRateLimitStore()
    return RateLimiter(policy=policy, store=store)


def rate_limited_response(
    decision: RateLimitDecision,
    *,
    request_id: str | None,
) -> JSONResponse:
    details = {
        "rule_key": decision.rule_key,
        "limit": decision.limit,
        "remaining": decision.remaining,
        "retry_after_seconds": decision.reset_seconds,
        "window_seconds": decision.window_seconds,
        "scope": decision.scope,
    }
    content = {
        "data": None,
        "error": {
            "code": "rate_limited",
            "message": "Rate limit exceeded.",
            "details": public_jsonable(details),
            "workflow_id": None,
            "request_id": request_id,
        },
    }
    headers = {
        "Retry-After": str(decision.reset_seconds),
        "X-RateLimit-Limit": str(decision.limit),
        "X-RateLimit-Remaining": str(decision.remaining),
        "X-RateLimit-Reset": str(decision.reset_seconds),
    }
    if request_id:
        headers["X-Request-ID"] = request_id
    return JSONResponse(status_code=429, headers=headers, content=content)


def _matching_rules(
    policy: RateLimitPolicy,
    *,
    method: str,
    path: str,
) -> list[RateLimitRule]:
    return [
        rule
        for rule in policy.rules
        if rule.enabled
        and (not rule.methods or method in {item.upper() for item in rule.methods})
        and any(path.startswith(prefix) for prefix in rule.path_prefixes)
    ]


def _counter_key(rule: RateLimitRule, *, identity: str) -> str:
    raw = f"{rule.key}:{rule.scope}:{identity}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _request_identity(
    request: Request,
    *,
    settings: Settings,
    scope: str,
) -> str:
    token = _bearer_token(request) or request.cookies.get(settings.auth_cookie_name)
    if scope == "session_or_ip" and token:
        return "session:" + hashlib.sha256(token.encode("utf-8")).hexdigest()
    client_host = request.client.host if request.client else "unknown"
    return f"ip:{client_host}"


def _bearer_token(request: Request) -> str | None:
    header = request.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()
