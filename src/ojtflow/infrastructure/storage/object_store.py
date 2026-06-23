"""Object storage adapters for uploaded artifact and dataset bytes."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from urllib.parse import urlparse

import urllib3

from ojtflow.config import Settings
from ojtflow.core.errors import OJTFlowError

try:
    from minio import Minio
    from minio.error import S3Error
except ImportError:  # pragma: no cover - dependency is installed in supported images.
    Minio = None  # type: ignore[assignment]

    class S3Error(Exception):
        pass


@dataclass(frozen=True)
class MinioObjectStore:
    """Small MinIO/S3-compatible byte-store wrapper.

    Postgres remains the metadata store. This adapter owns only raw bytes and returns
    stable ``s3://bucket/object`` references for metadata rows.
    """

    endpoint: str
    access_key: str
    secret_key: str
    bucket: str
    region: str = "us-east-1"
    secure: bool = False

    def __post_init__(self) -> None:
        if Minio is None:
            raise OJTFlowError(
                "MinIO object storage requires the 'minio' Python package."
            )
        missing = [
            name
            for name, value in {
                "OJT_MINIO_ENDPOINT": self.endpoint,
                "OJT_MINIO_ACCESS_KEY": self.access_key,
                "OJT_MINIO_SECRET_KEY": self.secret_key,
                "OJT_MINIO_BUCKET": self.bucket,
            }.items()
            if not str(value or "").strip()
        ]
        if missing:
            raise OJTFlowError("MinIO object storage is not configured: " + ", ".join(missing))
        object.__setattr__(self, "_client", self._build_client())
        object.__setattr__(self, "_bucket_checked", False)

    @classmethod
    def from_settings(cls, settings: Settings) -> "MinioObjectStore":
        return cls(
            endpoint=_minio_endpoint(settings.minio_endpoint),
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            bucket=settings.minio_bucket,
            region=settings.minio_region,
            secure=settings.minio_secure,
        )

    def put_bytes(
        self,
        *,
        object_key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> str:
        key = _clean_object_key(object_key)
        self.ensure_bucket()
        try:
            self._client.put_object(
                self.bucket,
                key,
                BytesIO(data),
                length=len(data),
                content_type=content_type or "application/octet-stream",
                metadata=metadata or {},
            )
        except S3Error as exc:
            raise OJTFlowError("Failed to write object to MinIO.", details={"key": key}) from exc
        return f"s3://{self.bucket}/{key}"

    def get_bytes(self, storage_ref: str) -> bytes:
        bucket, key = parse_s3_storage_ref(storage_ref)
        if bucket != self.bucket:
            raise OJTFlowError(
                "Object storage bucket does not match configured MinIO bucket.",
                details={"bucket": bucket, "configured_bucket": self.bucket},
            )
        response = None
        try:
            response = self._client.get_object(bucket, key)
            return response.read()
        except S3Error as exc:
            raise OJTFlowError("Failed to read object from MinIO.", details={"key": key}) from exc
        finally:
            if response is not None:
                response.close()
                response.release_conn()

    def ensure_bucket(self) -> None:
        if getattr(self, "_bucket_checked", False):
            return
        try:
            if not self._client.bucket_exists(self.bucket):
                self._client.make_bucket(self.bucket, location=self.region)
        except S3Error as exc:
            raise OJTFlowError(
                "MinIO bucket is unavailable.",
                details={"bucket": self.bucket, "endpoint": self.endpoint},
            ) from exc
        object.__setattr__(self, "_bucket_checked", True)

    def _build_client(self):
        return Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure,
            region=self.region,
            cert_check=False,
            http_client=urllib3.PoolManager(
                timeout=urllib3.Timeout(connect=2.0, read=20.0),
                retries=False,
            ),
        )


def build_object_store(settings: Settings) -> MinioObjectStore | None:
    if settings.object_storage_backend == "local":
        return None
    if settings.object_storage_backend == "minio":
        return MinioObjectStore.from_settings(settings)
    raise OJTFlowError(
        f"Unsupported object storage backend: {settings.object_storage_backend}"
    )


def parse_s3_storage_ref(storage_ref: str) -> tuple[str, str]:
    parsed = urlparse(storage_ref)
    if parsed.scheme != "s3" or not parsed.netloc or not parsed.path.strip("/"):
        raise OJTFlowError("Invalid S3 object storage reference.")
    return parsed.netloc, parsed.path.lstrip("/")


def is_s3_storage_ref(storage_ref: str) -> bool:
    return urlparse(storage_ref).scheme == "s3"


def _minio_endpoint(value: str) -> str:
    endpoint = value.strip()
    parsed = urlparse(endpoint)
    if parsed.scheme:
        endpoint = parsed.netloc + parsed.path
    return endpoint.strip("/")


def _clean_object_key(value: str) -> str:
    key = value.strip().lstrip("/")
    if not key or ".." in key.split("/"):
        raise OJTFlowError("Invalid object storage key.")
    return key
