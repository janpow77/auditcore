from datetime import timedelta
from io import BytesIO

import pytest
from PIL import Image

from auditcore_account import AccountError, AssetService, Crop, Extension, Field, ImagePolicy
from auditcore_account.welcome import welcome_html


def test_extensions_independent_unknown_fields_and_version(app):
    app.registry.register(
        Extension(
            "rechnungslegung.programm",
            1,
            "Operationelles Programm",
            (Field("cci", "CCI", True),),
            "program.read",
            "program.write",
            lambda values: None,
        )
    )
    role = app.admin.save_role(
        app.actor,
        app.tenant.id,
        "Programm",
        frozenset({"tenant.read", "program.read", "program.write"}),
    )
    app.admin.update_member(app.actor, app.member.id, 1, (role.id,), True)
    app.settings.save(
        app.user_actor, app.tenant.id, "rechnungslegung.programm", 0, 1, {"cci": "TEST"}
    )
    app.settings.save(app.actor, app.tenant.id, "branding", 0, 1, {})
    assert app.settings.read(app.user_actor, app.tenant.id, "rechnungslegung.programm").fields == {
        "cci": "TEST"
    }
    with pytest.raises(AccountError):
        app.settings.save(
            app.user_actor, app.tenant.id, "rechnungslegung.programm", 1, 2, {"cci": "X"}
        )
    with pytest.raises(AccountError):
        app.settings.save(
            app.user_actor,
            app.tenant.id,
            "rechnungslegung.programm",
            1,
            1,
            {"cci": "X", "extra": "Y"},
        )


@pytest.mark.parametrize(
    "values",
    [{"primary": "#ffffff"}, {"heading_font": "untrusted"}, {"primary": "url(x)"}, {"extra": "x"}],
)
def test_branding_validation(app, values):
    with pytest.raises(AccountError):
        app.settings.save(app.actor, app.tenant.id, "branding", 0, 1, values)
    assert (app.tenant.id, "branding") not in app.repo.snapshot().settings


def test_welcome_escapes_html_and_rejects_unknown_placeholder(app):
    assert "<script>" not in welcome_html("<script>alert(1)</script>")
    with pytest.raises(AccountError):
        app.settings.save(app.actor, app.tenant.id, "welcome", 0, 1, {"body": "{{password}}"})
    app.settings.acknowledge_welcome(app.user_actor, app.member.id)
    assert app.repo.snapshot().memberships[app.member.id].welcome_seen


def images(app):
    return AssetService(app.runtime, ImagePolicy(100000, 1000000, 128, 32, timedelta(minutes=10)))


def image_bytes():
    stream = BytesIO()
    image = Image.new("RGB", (200, 100), "red")
    image.save(stream, format="PNG")
    return stream.getvalue()


def test_image_sanitized_cropped_and_attached_atomically(app):
    service = images(app)
    asset = service.upload(app.user_actor, image_bytes(), crop=Crop(0, 0, 1))
    with Image.open(BytesIO(service.read(app.user_actor, asset))) as result:
        assert result.size == (100, 100)
        assert not result.getexif()
    app.profiles.update(app.user_actor, "account", app.user.id, 1, {}, image_id=asset)
    app.now[0] += timedelta(hours=1)
    assert service.purge_drafts() == 0
    assert service.read(app.user_actor, asset)


def test_image_foreign_tenant_and_expired_draft_denied(app):
    service = images(app)
    asset = service.upload(app.actor, image_bytes(), tenant_id=app.tenant.id)
    with pytest.raises(AccountError):
        app.profiles.update(app.user_actor, "account", app.user.id, 1, {}, image_id=asset)
    app.now[0] += timedelta(hours=1)
    with pytest.raises(AccountError):
        service.read(app.actor, asset)
    assert service.purge_drafts() == 1


@pytest.mark.parametrize("data", [b"", b'<svg onload="evil()"/>', b"%PDF-1.7"])
def test_invalid_images_rejected(app, data):
    with pytest.raises(AccountError):
        images(app).upload(app.user_actor, data)
