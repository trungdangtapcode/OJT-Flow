"""GPU-backed MedSigLIP FastAPI model service."""

from __future__ import annotations

import base64
import os
import time
from dataclasses import dataclass
from io import BytesIO
from threading import Lock
from typing import Any

from fastapi import FastAPI, HTTPException, Response
from PIL import Image, UnidentifiedImageError
from prometheus_client import Counter, Gauge, Histogram, CONTENT_TYPE_LATEST, generate_latest
from transformers import AutoModel, AutoProcessor
import torch

from ojtflow.core.contracts.medsiglip import (
    MedSiglipClassificationRequest,
    MedSiglipClassificationResult,
    MedSiglipImageClassification,
    MedSiglipPrediction,
)


MODEL_ID = (os.getenv("OJT_MEDSIGLIP_MODEL") or "google/medsiglip-448").strip()
CACHE_DIR = (os.getenv("OJT_MEDSIGLIP_CACHE_DIR") or "").strip() or None
REQUESTS = Counter(
    "medsiglip_requests_total",
    "Total MedSigLIP classification requests.",
    ("status",),
)
REQUEST_LATENCY = Histogram(
    "medsiglip_request_duration_seconds",
    "MedSigLIP classification latency in seconds.",
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60, 120),
)
REQUEST_IMAGES = Counter(
    "medsiglip_request_images_total",
    "Total images classified by MedSigLIP.",
)
REQUEST_LABELS = Counter(
    "medsiglip_request_labels_total",
    "Total candidate text labels scored by MedSigLIP.",
)
MODEL_LOADED = Gauge("medsiglip_model_loaded", "Whether the MedSigLIP model is loaded.")
CUDA_AVAILABLE = Gauge("medsiglip_cuda_available", "Whether torch sees CUDA.")


@dataclass
class MedSiglipRuntime:
    model: Any
    processor: Any
    device: str


_runtime: MedSiglipRuntime | None = None
_runtime_lock = Lock()
app = FastAPI(title="OJTFlow MedSigLIP", version="0.1.0")


@app.on_event("startup")
def startup() -> None:
    CUDA_AVAILABLE.set(1 if torch.cuda.is_available() else 0)
    if _parse_bool(os.getenv("OJT_MEDSIGLIP_PRELOAD"), default=True):
        _get_runtime()


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok" if _runtime is not None else "starting",
        "model": MODEL_ID,
        "model_loaded": _runtime is not None,
        "device": _runtime.device if _runtime else _resolve_device(load_check=False),
        "cuda_available": torch.cuda.is_available(),
    }


@app.get("/metrics")
def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/classify", response_model=MedSiglipClassificationResult)
def classify(request: MedSiglipClassificationRequest) -> MedSiglipClassificationResult:
    started_at = time.monotonic()
    try:
        result = _classify(request, started_at=started_at)
    except HTTPException:
        REQUESTS.labels(status="error").inc()
        raise
    except Exception as exc:  # pragma: no cover - service runtime guard
        REQUESTS.labels(status="error").inc()
        raise HTTPException(
            status_code=500,
            detail={"message": "MedSigLIP inference failed.", "error_type": type(exc).__name__},
        ) from exc
    REQUESTS.labels(status="ok").inc()
    REQUEST_LATENCY.observe(time.monotonic() - started_at)
    REQUEST_IMAGES.inc(len(request.images))
    REQUEST_LABELS.inc(len(request.candidate_labels))
    return result


def _classify(
    request: MedSiglipClassificationRequest,
    *,
    started_at: float,
) -> MedSiglipClassificationResult:
    runtime = _get_runtime()
    images = [_decode_image(image.image_base64) for image in request.images]
    inputs = runtime.processor(
        text=request.candidate_labels,
        images=images,
        padding="max_length",
        truncation=True,
        return_tensors="pt",
    )
    inputs = {key: value.to(runtime.device) for key, value in inputs.items()}
    with torch.no_grad():
        outputs = runtime.model(**inputs)
    logits_per_image = getattr(outputs, "logits_per_image", None)
    if logits_per_image is None:
        raise RuntimeError("MedSigLIP model output did not include logits_per_image.")
    probabilities = torch.softmax(logits_per_image, dim=1).detach().float().cpu()
    image_embeddings = _optional_tensor_list(
        getattr(outputs, "image_embeds", None),
        include=request.include_embeddings,
    )
    text_embeddings = _optional_tensor_list(
        getattr(outputs, "text_embeds", None),
        include=request.include_embeddings,
    )

    classifications: list[MedSiglipImageClassification] = []
    for image_index, row in enumerate(probabilities):
        predictions = [
            MedSiglipPrediction(label=label, score=float(row[label_index].item()))
            for label_index, label in enumerate(request.candidate_labels)
        ]
        predictions.sort(key=lambda prediction: prediction.score, reverse=True)
        classifications.append(
            MedSiglipImageClassification(
                image_index=image_index,
                source_ref=request.images[image_index].source_ref,
                predictions=predictions,
                image_embedding=image_embeddings[image_index]
                if image_embeddings is not None
                else None,
            )
        )

    return MedSiglipClassificationResult(
        model=MODEL_ID,
        device=runtime.device,
        classifications=classifications,
        text_embeddings=text_embeddings,
        elapsed_ms=(time.monotonic() - started_at) * 1000,
        limitations=[
            "Scores are zero-shot image-text similarity outputs, not a medical diagnosis.",
            "Clinical use requires review under the active OJTFlow governance policy.",
        ],
    )


def _get_runtime() -> MedSiglipRuntime:
    global _runtime
    if _runtime is not None:
        return _runtime
    with _runtime_lock:
        if _runtime is not None:
            return _runtime
        device = _resolve_device(load_check=True)
        token = os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_HUB_TOKEN") or None
        kwargs: dict[str, Any] = {"cache_dir": CACHE_DIR, "token": token}
        processor = AutoProcessor.from_pretrained(MODEL_ID, **kwargs)
        model_kwargs = dict(kwargs)
        if device.startswith("cuda"):
            model_kwargs["torch_dtype"] = torch.float16
        model = AutoModel.from_pretrained(MODEL_ID, **model_kwargs)
        model = model.to(device)
        model.eval()
        _runtime = MedSiglipRuntime(model=model, processor=processor, device=device)
        MODEL_LOADED.set(1)
        return _runtime


def _resolve_device(*, load_check: bool) -> str:
    requested = (os.getenv("OJT_MEDSIGLIP_DEVICE") or "cuda").strip().lower()
    require_gpu = _parse_bool(os.getenv("OJT_MEDSIGLIP_REQUIRE_GPU"), default=True)
    if requested == "auto":
        requested = "cuda" if torch.cuda.is_available() else "cpu"
    if requested.startswith("cuda") and not torch.cuda.is_available():
        if require_gpu and load_check:
            raise RuntimeError("CUDA is required for MedSigLIP but is not available.")
        return "cpu"
    if requested not in {"cpu", "cuda"} and not requested.startswith("cuda:"):
        raise RuntimeError("OJT_MEDSIGLIP_DEVICE must be cpu, cuda, cuda:N, or auto.")
    return requested


def _decode_image(image_base64: str) -> Image.Image:
    raw = image_base64.strip()
    if raw.startswith("data:") and "," in raw:
        raw = raw.split(",", 1)[1]
    try:
        data = base64.b64decode(raw, validate=True)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={"message": "image_base64 is not valid base64."},
        ) from exc
    try:
        with Image.open(BytesIO(data)) as image:
            return image.convert("RGB")
    except UnidentifiedImageError as exc:
        raise HTTPException(
            status_code=422,
            detail={"message": "image_base64 did not decode to a supported image."},
        ) from exc


def _optional_tensor_list(tensor: Any, *, include: bool) -> list[list[float]] | None:
    if not include or tensor is None:
        return None
    return tensor.detach().float().cpu().tolist()


def _parse_bool(value: str | None, *, default: bool) -> bool:
    if value is None or value == "":
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise RuntimeError(f"Invalid boolean environment value: {value}")
