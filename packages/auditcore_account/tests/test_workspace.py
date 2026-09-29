import pytest

from auditcore_account import AccountError


def test_workspace_form_contract_and_field_rights(app):
    items = app.workspace.list(app.user_actor, app.tenant.id)
    assert "profile" in {item["id"] for item in items}
    assert "new-account" not in {item["id"] for item in items}
    current = app.workspace.read(app.user_actor, "contact", app.tenant.id)
    assert next(f for f in current["fields"] if f["id"] == "function")["readonly"]
    with pytest.raises(AccountError):
        app.workspace.save(app.user_actor, "contact", 1, {"function": "Chef"}, app.tenant.id)
    result = app.workspace.save(app.user_actor, "profile", 1, {"title": "Dr."})
    assert result.document["values"]["title"] == "Dr."
    assert result.document["revision"] == 2


def test_admin_create_form_and_secret_result_not_in_document(app):
    result = app.workspace.save(
        app.actor, "new-account", 0, {"login": "new@example.invalid", "display_name": "Neu"}
    )
    assert result.document["values"] == {}
    access = "access/" + app.user.id
    result = app.workspace.save(app.actor, access, 1, {"action": "invite", "tenant": app.tenant.id})
    assert result.delivery is not None
    assert result.delivery.token not in str(result.document)


def test_admin_direct_form_call_cannot_bypass_permissions(app):
    with pytest.raises(AccountError):
        app.workspace.read(app.user_actor, "new-account")
    with pytest.raises(AccountError):
        app.workspace.read(app.user_actor, "access/" + app.user.id)


def test_revoking_own_tenant_membership_still_reports_success(app):
    app.admin.update_member(app.actor, app.member.id, 1, (app.tenant.id + ":admin",), True)
    result = app.workspace.save(
        app.user_actor,
        "member/" + app.member.id,
        2,
        {"roles": "", "active": "false"},
        app.tenant.id,
    )
    assert result.document["title"] == "Änderungen gespeichert"
    assert not result.document["editable"]
    assert not app.repo.snapshot().memberships[app.member.id].active
