"""Redis-backed session cache with a local fallback for development."""

from __future__ import annotations

import json
import time
from copy import deepcopy
from typing import Any

from ojtflow.core.errors import DependencyUnavailableError

try:
    import redis
    from redis.exceptions import RedisError
except ImportError:  # pragma: no cover
    redis = None

    class RedisError(Exception):
        pass


class InMemorySessionCache:
    """Process-local cache for tests and single-process development."""

    def __init__(self) -> None:
        self._fallback_sessions: dict[str, tuple[float, dict[str, Any]]] = {}
        self._fallback_states: dict[str, tuple[float, dict[str, Any]]] = {}

    def set_session(self, token_hash: str, payload: dict[str, Any], ttl_seconds: int) -> None:
        self._fallback_sessions[token_hash] = (time.time() + ttl_seconds, deepcopy(payload))

    def get_session(self, token_hash: str) -> dict[str, Any] | None:
        item = self._fallback_sessions.get(token_hash)
        if not item:
            return None
        expires_at, payload = item
        if expires_at <= time.time():
            self._fallback_sessions.pop(token_hash, None)
            return None
        return deepcopy(payload)

    def delete_session(self, token_hash: str) -> None:
        self._fallback_sessions.pop(token_hash, None)

    def set_oauth_state(
        self,
        state: str,
        ttl_seconds: int,
        payload: dict[str, Any] | None = None,
    ) -> None:
        self._fallback_states[state] = (time.time() + ttl_seconds, payload or {})

    def consume_oauth_state(self, state: str) -> dict[str, Any] | None:
        item = self._fallback_states.pop(state, None)
        if not item:
            return None
        expires_at, payload = item
        return deepcopy(payload) if expires_at > time.time() else None


class RedisSessionCache:
    """Caches active sessions and short-lived OAuth state values."""

    def __init__(self, redis_url: str, *, allow_fallback: bool = True) -> None:
        self.redis_url = redis_url
        self._client_error: Exception | None = None
        if not redis_url:
            self._client = None
        else:
            try:
                self._client = redis.from_url(redis_url, decode_responses=True) if redis else None
            except (RedisError, ValueError) as exc:
                self._client = None
                self._client_error = exc
        self.allow_fallback = allow_fallback
        self._fallback = InMemorySessionCache()

    def set_session(self, token_hash: str, payload: dict[str, Any], ttl_seconds: int) -> None:
        key = self._session_key(token_hash)
        try:
            if self._client:
                self._client.setex(key, ttl_seconds, json.dumps(payload))
                return
        except RedisError as exc:
            self._raise_or_fallback("set_session", exc)
        self._raise_or_fallback("set_session")
        self._fallback.set_session(token_hash, payload, ttl_seconds)

    def get_session(self, token_hash: str) -> dict[str, Any] | None:
        key = self._session_key(token_hash)
        try:
            if self._client:
                raw = self._client.get(key)
                try:
                    return json.loads(raw) if raw else None
                except json.JSONDecodeError:
                    self._delete_corrupt_key(key)
                    return None
        except RedisError as exc:
            self._raise_or_fallback("get_session", exc)
        self._raise_or_fallback("get_session")
        return self._fallback.get_session(token_hash)

    def delete_session(self, token_hash: str) -> None:
        key = self._session_key(token_hash)
        try:
            if self._client:
                self._client.delete(key)
        except RedisError as exc:
            self._raise_or_fallback("delete_session", exc)
        if self._client is None:
            self._raise_or_fallback("delete_session")
        self._fallback.delete_session(token_hash)

    def set_oauth_state(
        self,
        state: str,
        ttl_seconds: int,
        payload: dict[str, Any] | None = None,
    ) -> None:
        key = self._state_key(state)
        value = json.dumps(payload or {})
        try:
            if self._client:
                self._client.setex(key, ttl_seconds, value)
                return
        except RedisError as exc:
            self._raise_or_fallback("set_oauth_state", exc)
        self._raise_or_fallback("set_oauth_state")
        self._fallback.set_oauth_state(state, ttl_seconds, payload)

    def consume_oauth_state(self, state: str) -> dict[str, Any] | None:
        key = self._state_key(state)
        try:
            if self._client:
                if hasattr(self._client, "getdel"):
                    raw = self._client.getdel(key)
                    return json.loads(raw) if raw else None
                raw = self._client.get(key)
                if raw:
                    self._client.delete(key)
                    return json.loads(raw)
                return None
        except RedisError as exc:
            self._raise_or_fallback("consume_oauth_state", exc)
        except json.JSONDecodeError:
            self._delete_corrupt_key(key)
            return None
        self._raise_or_fallback("consume_oauth_state")
        return self._fallback.consume_oauth_state(state)

    def _raise_or_fallback(self, operation: str, exc: Exception | None = None) -> None:
        if self.allow_fallback:
            return
        cause = exc or self._client_error
        details = {
            "dependency": "redis",
            "operation": operation,
        }
        if cause is not None:
            details["error_type"] = type(cause).__name__
        raise DependencyUnavailableError(
            "Redis session cache is unavailable.",
            details=details,
        )

    def _delete_corrupt_key(self, key: str) -> None:
        try:
            if self._client:
                self._client.delete(key)
        except RedisError:
            pass

    def _session_key(self, token_hash: str) -> str:
        return f"ojtflow:session:{token_hash}"

    def _state_key(self, state: str) -> str:
        return f"ojtflow:oauth_state:{state}"
