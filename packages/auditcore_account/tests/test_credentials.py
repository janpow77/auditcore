from datetime import timedelta

import pytest

from auditcore_account import AccountError, InvitationService

SECRET = "Testpasswort-12345"


def invitation(app):
    service = InvitationService(app.credentials)
    return service, service.issue(app.actor, app.user.id, app.tenant.id, timedelta(hours=1))


def test_invitation_hash_snapshot_and_one_time_redemption(app):
    service, issued = invitation(app)
    assert issued.token not in repr(app.repo.snapshot())
    assert "Alex Beispiel" in issued.welcome_text
    app.settings.save(app.actor, app.tenant.id, "welcome", 0, 1, {"body": "Neuer Text"})
    assert "Neuer Text" not in issued.welcome_text
    actor = service.redeem(issued.token, SECRET)
    assert app.credentials.login(app.user.login, SECRET) == actor
    with pytest.raises(AccountError):
        service.redeem(issued.token, SECRET)


def test_expiry_rejects_and_does_not_consume(app):
    service, issued = invitation(app)
    app.now[0] += timedelta(hours=2)
    with pytest.raises(AccountError):
        service.redeem(issued.token, SECRET)
    assert not next(iter(app.repo.snapshot().grants.values())).used


def test_reset_revokes_prior_sessions_and_other_links(app):
    service, issued = invitation(app)
    another = service.issue(app.actor, app.user.id, app.tenant.id, timedelta(hours=1))
    actor = service.redeem(issued.token, SECRET)
    with pytest.raises(AccountError):
        service.redeem(another.token, SECRET)
    updated = app.credentials.change(actor, SECRET, SECRET + "!")
    assert updated.session_revision == actor.session_revision + 1
    with pytest.raises(AccountError):
        app.profiles.read(actor, "account", actor.account_id)
    assert app.credentials.login(app.user.login, SECRET + "!") == updated


def test_temporary_password_restricts_services_until_changed(app):
    app.credentials.provision(app.actor, app.user.id, SECRET, timedelta(hours=1))
    actor = app.credentials.login(app.user.login, SECRET)
    assert [x["id"] for x in app.workspace.list(actor)] == ["security"]
    with pytest.raises(AccountError):
        app.profiles.read(actor, "account", actor.account_id)
    result = app.workspace.save(
        actor, "security", 2, {"current": SECRET, "new": SECRET + "!", "confirmation": SECRET + "!"}
    )
    assert result.document["values"] == {}
    assert app.profiles.read(result.actor, "account", actor.account_id)


def test_tenant_admin_cannot_reset_global_password(app):
    app.admin.update_member(app.actor, app.member.id, 1, (app.tenant.id + ":admin",), True)
    service = InvitationService(app.credentials)
    with pytest.raises(AccountError):
        service.issue(
            app.user_actor, app.user.id, app.tenant.id, timedelta(hours=1), purpose="reset"
        )


def test_suspended_membership_revokes_invitation(app):
    service, issued = invitation(app)
    app.admin.update_member(app.actor, app.member.id, 1, app.member.role_ids, False)
    with pytest.raises(AccountError):
        service.redeem(issued.token, SECRET)


def test_wrong_current_password_does_not_mutate(app):
    service, issued = invitation(app)
    actor = service.redeem(issued.token, SECRET)
    with pytest.raises(AccountError):
        app.credentials.change(actor, "wrong", SECRET + "!")
    assert app.credentials.login(app.user.login, SECRET) == actor


def test_access_provision_rejects_revision_race(app, monkeypatch):
    key = "access/" + app.user.id
    form = app.workspace.read(app.actor, key)
    expected = form["revision"]
    provision = app.credentials.provision

    def concurrent_provision(actor, target, password, lifetime, expected_revision=None):
        provision(actor, target, SECRET, lifetime, expected_revision=expected)
        provision(
            actor,
            target,
            password,
            lifetime,
            expected_revision=expected_revision,
        )

    monkeypatch.setattr(app.credentials, "provision", concurrent_provision)
    with pytest.raises(AccountError, match="inzwischen geändert"):
        app.workspace.save(
            app.actor, key, expected, {"action": "provision", "password": SECRET + "!"}
        )

    assert app.credentials.login(app.user.login, SECRET)
    with pytest.raises(AccountError):
        app.credentials.login(app.user.login, SECRET + "!")


def test_access_invitation_rejects_stale_account_revision(app):
    key = "access/" + app.user.id
    expected = app.workspace.read(app.actor, key)["revision"]
    app.credentials.provision(app.actor, app.user.id, SECRET, timedelta(hours=1))
    with pytest.raises(AccountError, match="inzwischen geändert"):
        app.workspace.access.save(
            app.actor,
            key,
            expected,
            {"action": "invite", "tenant": app.tenant.id},
        )
    assert app.repo.snapshot().grants == {}
