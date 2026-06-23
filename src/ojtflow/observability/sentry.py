"""Sentry setup for API and worker runtimes."""

from __future__ import annotations

from ojtflow.config import Settings

_configured_runtimes: set[str] = set()


def configure_sentry(settings: Settings, *, runtime: str) -> None:
    """Enable Sentry when OJT_SENTRY_DSN is configured."""

    if not settings.sentry_dsn or runtime in _configured_runtimes:
        return
    try:
        import sentry_sdk  # type: ignore[import]
    except ImportError:
        return
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.product_mode,
        traces_sample_rate=0.05,
        send_default_pii=False,
        release="ojtflow@0.1.0",
    )
    sentry_sdk.set_tag("runtime", runtime)
    _configured_runtimes.add(runtime)
