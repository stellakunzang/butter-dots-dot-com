"""Sentry starts only with a DSN, and never sends user data or request bodies."""

import sentry_sdk

from app import monitoring
from app.config import settings


def test_no_dsn_sends_nothing(monkeypatch):
    calls = []
    monkeypatch.setattr(settings, "sentry_dsn", None)
    monkeypatch.setattr(sentry_sdk, "init", lambda **kw: calls.append(kw))

    assert monitoring.init_monitoring() is False
    assert calls == []


def test_dsn_starts_sentry_without_user_data(monkeypatch):
    calls = []
    monkeypatch.setattr(settings, "sentry_dsn", "https://key@example.ingest.sentry.io/1")
    monkeypatch.setattr(settings, "sentry_environment", None)
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("RENDER_SERVICE_ID", raising=False)
    monkeypatch.setattr(sentry_sdk, "init", lambda **kw: calls.append(kw))

    assert monitoring.init_monitoring() is True
    (options,) = calls
    assert options["send_default_pii"] is False
    assert options["max_request_body_size"] == "never"
    assert options["traces_sample_rate"] == 0.0
    assert options["environment"] == "local"


def test_render_reports_as_production(monkeypatch):
    calls = []
    monkeypatch.setattr(settings, "sentry_dsn", "https://key@example.ingest.sentry.io/1")
    monkeypatch.setattr(settings, "sentry_environment", None)
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setattr(sentry_sdk, "init", lambda **kw: calls.append(kw))

    monitoring.init_monitoring()
    assert calls[0]["environment"] == "production"
