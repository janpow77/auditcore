"""Tests für Fehlerklassen und Serialisierung."""

from __future__ import annotations

from auditcore_privacy import CollisionError, PrivacyError, ScopeError


def test_privacy_error_attributes() -> None:
    """Standardwerte und Attribute von PrivacyError."""
    err = PrivacyError("Fehler aufgetreten", code="PRIVACY_ERROR", details={"field": "test"})
    assert err.status == 400
    assert err.code == "PRIVACY_ERROR"
    assert err.details == {"field": "test"}

    d = err.to_dict()
    assert d["error"]["code"] == "PRIVACY_ERROR"
    assert d["error"]["message"] == "Fehler aufgetreten"
    assert d["error"]["details"] == {"field": "test"}
    assert err.to_json() == d


def test_scope_error_and_collision_error() -> None:
    """ScopeError und CollisionError erben von PrivacyError."""
    scope_err = ScopeError("Scope nicht gefunden", code="SCOPE_NOT_FOUND")
    assert scope_err.status == 404
    assert isinstance(scope_err, PrivacyError)

    coll_err = CollisionError("Kollision")
    assert coll_err.status == 409
    assert isinstance(coll_err, PrivacyError)
