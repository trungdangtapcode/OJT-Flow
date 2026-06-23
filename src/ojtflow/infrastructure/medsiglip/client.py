"""HTTP client for the GPU-backed MedSigLIP model service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from ojtflow.core.contracts.medsiglip import (
    MedSiglipClassificationRequest,
    MedSiglipClassificationResult,
    MedSiglipServiceStatus,
)
from ojtflow.core.errors import DependencyUnavailableError, ToolExecutionError


@dataclass(frozen=True)
class MedSiglipClientConfig:
    """Runtime configuration for the MedSigLIP model service."""

    enabled: bool
    base_url: str
    model: str
    timeout_seconds: float


class MedSiglipClient:
    """Small adapter around the local MedSigLIP HTTP service."""

    def __init__(self, config: MedSiglipClientConfig) -> None:
        self.config = config

    def classify(
        self,
        request: MedSiglipClassificationRequest,
    ) -> MedSiglipClassificationResult:
        self._require_configured()
        payload = request.model_dump(mode="json")
        try:
            with httpx.Client(
                base_url=self.config.base_url,
                timeout=self.config.timeout_seconds,
            ) as client:
                response = client.post("/classify", json=payload)
        except httpx.HTTPError as exc:
            raise DependencyUnavailableError(
                "MedSigLIP service is unavailable.",
                details={"error_type": type(exc).__name__},
            ) from exc

        if response.status_code >= 500:
            raise DependencyUnavailableError(
                "MedSigLIP service failed to process the request.",
                details={
                    "status_code": response.status_code,
                    "model": self.config.model,
                },
            )
        if response.status_code >= 400:
            raise ToolExecutionError(
                "MedSigLIP request was rejected by the model service.",
                details={
                    "status_code": response.status_code,
                    "model": self.config.model,
                },
            )
        return MedSiglipClassificationResult.model_validate(response.json())

    def status(self) -> MedSiglipServiceStatus:
        if not self.config.enabled:
            return MedSiglipServiceStatus(
                status="disabled",
                enabled=False,
                model=self.config.model,
                base_url_configured=bool(self.config.base_url),
            )
        if not self.config.base_url:
            return MedSiglipServiceStatus(
                status="unavailable",
                enabled=True,
                model=self.config.model,
                base_url_configured=False,
                detail="OJT_MEDSIGLIP_BASE_URL is not configured.",
            )
        try:
            with httpx.Client(
                base_url=self.config.base_url,
                timeout=min(self.config.timeout_seconds, 10.0),
            ) as client:
                response = client.get("/health")
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            return MedSiglipServiceStatus(
                status="unavailable",
                enabled=True,
                model=self.config.model,
                base_url_configured=True,
                service_url=self.config.base_url,
                detail=type(exc).__name__,
            )
        return MedSiglipServiceStatus(
            status="ok",
            enabled=True,
            model=str(payload.get("model") or self.config.model),
            base_url_configured=True,
            service_url=self.config.base_url,
            device=str(payload.get("device") or "") or None,
        )

    def _require_configured(self) -> None:
        if not self.config.enabled:
            raise DependencyUnavailableError("MedSigLIP integration is disabled.")
        if not self.config.base_url:
            raise DependencyUnavailableError(
                "MedSigLIP service URL is not configured.",
                details={"setting": "OJT_MEDSIGLIP_BASE_URL"},
            )
