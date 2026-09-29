import pytest

from auditcore_account import AccountError, Actor


def test_profile_revision_and_atomic_rollback(app):
    changed = app.profiles.update(app.user_actor, "account", app.user.id, 1, {"title": "Dr."})
    assert changed.revision == 2
    with pytest.raises(AccountError, match="inzwischen"):
        app.profiles.update(app.user_actor, "account", app.user.id, 1, {"title": "Prof."})
    assert app.repo.snapshot().accounts[app.user.id].fields["title"] == "Dr."
    assert app.repo.snapshot().events[-1].fields == ("title",)
    assert "Dr." not in repr(app.repo.snapshot().events)


def test_own_contact_but_no_function_edit(app):
    app.profiles.update(app.user_actor, "membership", app.member.id, 1, {"phone": "123"})
    with pytest.raises(AccountError):
        app.profiles.update(app.user_actor, "membership", app.member.id, 2, {"function": "Chef"})


def test_cross_tenant_and_cross_account_denied(app):
    other = app.admin.create_tenant(
        app.actor, "andere", {"official_name": "Andere", "display_name": "Andere"}
    )
    for kind, key in [("tenant", other.id), ("account", app.actor.account_id)]:
        with pytest.raises(AccountError):
            app.profiles.read(app.user_actor, kind, key)
    with pytest.raises(AccountError):
        app.admin.add_member(app.user_actor, other.id, app.user.id, (other.id + ":admin",))


def test_read_members_permission_does_not_allow_edit(app):
    role = app.admin.save_role(
        app.actor, app.tenant.id, "Lesen", frozenset({"tenant.read", "membership.read"})
    )
    app.admin.update_member(app.actor, app.member.id, 1, (role.id,), True)
    other = app.admin.create_account(app.actor, "other@example.invalid", "Andere Person")
    member = app.admin.add_member(app.actor, app.tenant.id, other.id, (app.tenant.id + ":member",))
    assert app.profiles.read(app.user_actor, "membership", member.id).editable == ()
    with pytest.raises(AccountError):
        app.profiles.update(app.user_actor, "membership", member.id, 1, {"phone": "123"})


def test_cross_tenant_role_and_escalation_denied(app):
    other = app.admin.create_tenant(
        app.actor, "andere", {"official_name": "Andere", "display_name": "Andere"}
    )
    with pytest.raises(AccountError):
        app.admin.update_member(app.actor, app.member.id, 1, (other.id + ":admin",), True)
    with pytest.raises(AccountError):
        app.admin.save_role(app.user_actor, app.tenant.id, "Höher", frozenset({"role.create"}))
    assert app.repo.snapshot().memberships[app.member.id].revision == 1


def test_last_platform_admin_protected(app):
    with pytest.raises(AccountError):
        app.admin.suspend_account(app.actor, app.actor.account_id, 1)
    assert app.repo.snapshot().accounts[app.actor.account_id].active


def test_membership_and_account_suspension_have_different_scope(app):
    app.admin.update_member(app.actor, app.member.id, 1, app.member.role_ids, False)
    assert app.profiles.read(app.user_actor, "account", app.user.id)
    with pytest.raises(AccountError):
        app.profiles.read(app.user_actor, "tenant", app.tenant.id)
    app.admin.suspend_account(app.actor, app.user.id, 1)
    with pytest.raises(AccountError):
        app.profiles.read(app.user_actor, "account", app.user.id)


def test_external_profile_and_password_managed_elsewhere(app):
    account = app.admin.create_account(app.actor, "sso@example.invalid", "SSO", external=True)
    actor = Actor(account.id, 1)
    assert not app.profiles.read(actor, "account", account.id).editable
    with pytest.raises(AccountError):
        app.profiles.update(actor, "account", account.id, 1, {"display_name": "Neu"})


def test_repository_does_not_leak_mutable_state(app):
    snapshot = app.repo.snapshot()
    snapshot.accounts.clear()
    assert app.repo.snapshot().accounts
    with pytest.raises(RuntimeError), app.repo.transaction() as state:
        state.accounts.clear()
        raise RuntimeError("Rollback")
    assert app.repo.snapshot().accounts


def test_platform_access_change_invalidates_sessions_and_preserves_last_admin(app):
    app.admin.set_account_access(app.actor, app.user.id, 1, active=True, platform_admin=True)
    new_admin = Actor(app.user.id, 2)
    result = app.workspace.save(
        app.actor,
        "status/" + app.actor.account_id,
        1,
        {"active": "true", "platform_admin": "false"},
    )
    assert result.reauthenticate
    with pytest.raises(AccountError):
        app.profiles.read(app.actor, "account", app.actor.account_id)
    with pytest.raises(AccountError):
        app.admin.set_account_access(new_admin, app.user.id, 2, active=False, platform_admin=True)


def test_first_visit_welcome_is_per_membership(app):
    assert "Alex Beispiel" in app.settings.first_visit_welcome(app.user_actor, app.tenant.id)
    app.settings.acknowledge_welcome(app.user_actor, app.member.id)
    assert app.settings.first_visit_welcome(app.user_actor, app.tenant.id) is None
