"""Rate limiting contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel, NonBlankStr


RateLimitScope = Literal["ip", "session_or_ip"]


class RateLimitRule(ContractModel):
    """One route-category rate limit rule."""

    key: NonBlankStr
    description: NonBlankStr
    methods: list[NonBlankStr] = Field(default_factory=list)
    path_prefixes: list[NonBlankStr] = Field(default_factory=list)
    limit: int = Field(gt=0)
    window_seconds: int = Field(gt=0)
    scope: RateLimitScope = "session_or_ip"
    enabled: bool = True


class RateLimitPolicy(ContractModel):
    """Data-driven API rate limit policy."""

    version: NonBlankStr = "rate_limit_policy.v1"
    rules: list[RateLimitRule] = Field(default_factory=list)


class RateLimitDecision(ContractModel):
    """Result of one rate-limit check."""

    allowed: bool
    rule_key: str
    limit: int
    remaining: int
    reset_seconds: int
    window_seconds: int
    scope: RateLimitScope
