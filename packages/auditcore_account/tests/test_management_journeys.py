"""Vollständige Verwaltungsabläufe über denselben Vertrag wie die Frontends."""

from datetime import timedelta
from io import BytesIO

import pytest
from PIL import Image

from auditcore_account import AccountError, AssetService, Extension, Field, ImagePolicy


def test_platform_creates_tenant_and_assigns_existing_account(app):
    assert "new-tenant" in {i["id"] for i in app.workspace.list(app.actor)}
    app.workspace.save(
        app.actor,
        "new-tenant",
        0,
        {"slug": "neu", "official_name": "Neue Organisation", "display_name": "Neu"},
    )
    tenants = app.admin.list_tenants(app.actor)
    new = next(t for t in tenants if t.slug == "neu")
    assert new.id not in {t.id for t in app.admin.list_tenants(app.user_actor)}
    app.workspace.save(
        app.actor, "new-member", 0, {"login": app.user.login, "role_id": new.id + ":member"}, new.id
    )
    assert new.id not in {t.id for t in app.admin.list_tenants(app.user_actor)}
    result = app.workspace.save(app.actor, "tenant-status/" + new.id, 1, {"active": "true"})
    assert result.document["values"]["active"] == "true"
    assert new.id in {t.id for t in app.admin.list_tenants(app.user_actor)}
    with pytest.raises(AccountError):
        app.workspace.save(app.user_actor, "tenant", 2, {"city": "Berlin"}, new.id)
    profile = app.workspace.read(app.actor, "tenant", new.id)
    app.workspace.save(
        app.actor, "tenant", profile["revision"], {"city": "Berlin", "image_id": ""}, new.id
    )
    assert app.profiles.read(app.user_actor, "tenant", new.id).fields["city"] == "Berlin"


def test_custom_role_management_and_system_role_protection(app):
    items = app.workspace.list(app.actor, app.tenant.id)
    assert "new-role" in {i["id"] for i in items}
    assert "member/" + app.member.id in {i["id"] for i in items}
    app.workspace.save(
        app.actor, "new-role", 0, {"name": "Leser", "permissions": "tenant.read"}, app.tenant.id
    )
    role = next(r for r in app.repo.snapshot().roles.values() if r.name == "Leser")
    key = "role/" + role.id
    result = app.workspace.save(
        app.actor,
        key,
        1,
        {"name": "Lesende", "permissions": "tenant.read\nmembership.read"},
        app.tenant.id,
    )
    assert result.document["revision"] == 2
    assert result.document["values"]["name"] == "Lesende"
    protected = "role/" + app.tenant.id + ":admin"
    assert not app.workspace.read(app.actor, protected, app.tenant.id)["editable"]
    with pytest.raises(AccountError):
        app.admin.save_role(
            app.actor,
            app.tenant.id,
            "Manipuliert",
            frozenset({"tenant.read"}),
            role_id=app.tenant.id + ":admin",
            expected=1,
        )


def test_branding_and_greeting_are_separate_forms(app):
    branding = app.workspace.read(app.actor, "branding", app.tenant.id)
    assert {f["id"] for f in branding["fields"]} >= {"body_font", "logo_document"}
    result = app.workspace.save(app.actor, "branding", 0, {"body_font": "serif"}, app.tenant.id)
    assert result.document["values"]["body_font"] == "serif"
    welcome = app.workspace.read(app.actor, "welcome", app.tenant.id)
    assert welcome["revision"] == 0
    app.workspace.save(app.actor, "welcome", 0, {"body": "Hallo {{display_name}}"}, app.tenant.id)
    app.workspace.save(app.actor, "welcome", 1, {"on_first_visit": "false"}, app.tenant.id)
    assert app.settings.first_visit_welcome(app.user_actor, app.tenant.id) is None
    assert (
        app.workspace.read(app.user_actor, "branding", app.tenant.id)["values"]["body_font"]
        == "serif"
    )


def test_registered_programme_form_roundtrip_and_unknown_namespace(app):
    app.registry.register(
        Extension(
            "rechnungslegung.programm",
            1,
            "Programm",
            (Field("cci", "CCI", True),),
            "tenant.read",
            "tenant.update",
            lambda values: None,
        )
    )
    form = app.workspace.read(app.actor, "rechnungslegung.programm", app.tenant.id)
    assert form["values"] == {}
    app.workspace.save(app.actor, "rechnungslegung.programm", 0, {"cci": "TEST"}, app.tenant.id)
    assert app.workspace.read(app.user_actor, "rechnungslegung.programm", app.tenant.id)[
        "values"
    ] == {"cci": "TEST"}
    with pytest.raises(AccountError):
        app.workspace.read(app.actor, "unknown.programme", app.tenant.id)


def test_start_password_form_does_not_return_secret(app):
    result = app.workspace.save(
        app.actor,
        "access/" + app.user.id,
        1,
        {"action": "provision", "password": "Startpasswort-12345"},
    )
    assert result.delivery is None
    assert result.document["values"] == {}
    actor = app.credentials.login(app.user.login, "Startpasswort-12345")
    with pytest.raises(AccountError):
        app.profiles.read(actor, "account", app.user.id)
    assert app.workspace.read(actor, "security")["editable"]


def test_tenant_picture_and_document_logo_are_authorized_assets(app):
    service = AssetService(
        app.runtime, ImagePolicy(100000, 1000000, 128, 32, timedelta(minutes=10))
    )
    stream = BytesIO()
    Image.new("RGB", (100, 100), "blue").save(stream, format="PNG")
    picture = service.upload(app.actor, stream.getvalue(), tenant_id=app.tenant.id)
    tenant = app.profiles.read(app.actor, "tenant", app.tenant.id)
    app.profiles.update(app.actor, "tenant", app.tenant.id, tenant.revision, {}, image_id=picture)
    logo = service.upload(app.actor, stream.getvalue(), tenant_id=app.tenant.id)
    app.settings.save(app.actor, app.tenant.id, "branding", 0, 1, {"logo_document": logo})
    assert service.read(app.user_actor, picture, preview=True)
    assert service.read(app.user_actor, logo)
    assert app.profiles.read(app.user_actor, "tenant", app.tenant.id).image_id == picture


@pytest.mark.parametrize("fields", [{"email": "ungueltig"}, {"website": "http://example.invalid"}])
def test_invalid_tenant_contact_does_not_overwrite_previous_data(app, fields):
    current = app.profiles.read(app.actor, "tenant", app.tenant.id)
    with pytest.raises(AccountError):
        app.profiles.update(app.actor, "tenant", app.tenant.id, current.revision, fields)
    assert app.profiles.read(app.actor, "tenant", app.tenant.id).revision == current.revision


def test_imported_tenant_only_administration_cannot_remove_last_admin(app):
    app.admin.update_member(app.actor, app.member.id, 1, (app.tenant.id + ":admin",), True)
    # Ein Host kann bestehende Mandanten ohne globale Plattformadministration importieren.
    with app.repo.transaction() as state:
        state.accounts[app.actor.account_id].platform_admin = False
    role = app.admin.save_role(app.user_actor, app.tenant.id, "Lesen", frozenset({"tenant.read"}))
    assert role.name == "Lesen"
    with pytest.raises(AccountError):
        app.admin.update_member(app.user_actor, app.member.id, 2, (role.id,), True)
    assert app.repo.snapshot().memberships[app.member.id].role_ids == (app.tenant.id + ":admin",)


def test_readback_failure_is_not_misreported_as_success(app, monkeypatch):
    original = app.workspace.read
    calls = 0

    def read(actor, key, tenant=""):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise AccountError("storage_unavailable", "Ablage nicht erreichbar")
        return original(actor, key, tenant)

    monkeypatch.setattr(app.workspace, "read", read)
    with pytest.raises(AccountError, match="Ablage nicht erreichbar"):
        app.workspace.save(app.actor, "profile", 1, {"title": "Dr."})
