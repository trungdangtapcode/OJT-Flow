"""Redis-backed session cache with a local fallback for development."""

from __future__ import annotations

import json
import time
from copy import deepcopy
from typing import Any

try:
    import redis
    from redis.exceptions import RedisError
except ImportError:  # pragma: no cover
    redis = None

    class RedisError(Exception):
        pass


class RedisSessionCache:
    """Caches active sessions and short-lived OAuth state values."""

    def __init__(self, redis_url: str) -> None:
        self.redis_url = redis_url
        self._client = redis.from_url(redis_url, decode_responses=True) if redis else None
        self._fallback_sessions: dict[str, tuple[float, dict[str, Any]]] = {}
        self._fallback_states: dict[str, tuple[float, dict[str, Any]]] = {}

    def set_session(self, token_hash: str, payload: dict[str, Any], ttl_seconds: int) -> None:
        key = self._session_key(token_hash)
        try:
            if self._client:
                self._client.setex(key, ttl_seconds, json.dumps(payload))
                return
        except RedisError:
            pass
        self._fallback_sessions[token_hash] = (time.time() + ttl_seconds, deepcopy(payload))

    def get_session(self, token_hash: str) -> dict[str, Any] | None:
        key = self._session_key(token_hash)
        try:
            if self._client:
                raw = self._client.get(key)
                return json.loads(raw) if raw else None
        except (RedisError, json.JSONDecodeError):
            pass
        item = self._fallback_sessions.get(token_hash)
        if not item:
            return None
        expires_at, payload = item
        if expires_at <= time.time():
            self._fallback_sessions.pop(token_hash, None)
            return None
        return deepcopy(payload)

    def delete_session(self, token_hash: str) -> None:
        key = self._session_key(token_hash)
        try:
            if self._client:
                self._client.delete(key)
        except RedisError:
            pass
        self._fallback_sessions.pop(token_hash, None)

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
        except RedisError:
            pass
        self._fallback_states[state] = (time.time() + ttl_seconds, payload or {})

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
        except (RedisError, json.JSONDecodeError):
            pass
        item = self._fallback_states.pop(state, None)
        if not item:
            return None
        expires_at, payload = item
        return deepcopy(payload) if expires_at > time.time() else None

    def _session_key(self, token_hash: str) -> str:
        return f"ojtflow:session:{token_hash}"

    def _state_key(self, state: str) -> str:
        return f"ojtflow:oauth_state:{state}"
