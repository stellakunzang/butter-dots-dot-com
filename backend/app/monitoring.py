"""
Error reporting to Sentry.

Off unless ``SENTRY_DSN`` is set, so local runs and tests send nothing. Only
unhandled errors are reported: no performance tracing, no user data, and no
request bodies, which carry the user's text or PDF.

An out-of-memory kill cannot be reported from inside the process it ends. That
case is covered by the uptime monitor (see docs/guides/MONITORING.md).
"""

from app.config import running_on_render, settings


def init_monitoring() -> bool:
    """Start Sentry if a DSN is configured. Returns whether it started."""
    if not settings.sentry_dsn:
        return False

    import sentry_sdk

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment
        or ("production" if running_on_render() else "local"),
        send_default_pii=False,
        max_request_body_size="never",
        traces_sample_rate=0.0,
    )
    return True
