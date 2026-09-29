from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from auditcore_account import (
    AccountError,
    Actor,
    AdminService,
    CredentialsService,
    ExtensionRegistry,
    MemoryRepository,
    ProfileService,
    Runtime,
    SettingsService,
    Workspace,
)


def password_policy(password: str) -> None:
    if len(password) < 12:
        raise AccountError("password_policy", "Mindestens zwölf Zeichen für diesen Test.")


@pytest.fixture
def app():
    repo = MemoryRepository()
    now = [datetime(2026, 9, 29, tzinfo=UTC)]
    runtime = Runtime(repo, lambda: now[0])
    admin = AdminService(runtime, frozenset({"program.read", "program.write"}))
    root = admin.bootstrap("root@example.invalid", "Plattform")
    actor = Actor(root.id, root.session_revision)
    tenant = admin.create_tenant(
        actor, "beispiel", {"official_name": "Beispiel GmbH", "display_name": "Beispiel"}
    )
    admin.set_tenant_active(actor, tenant.id, tenant.revision, True)
    user = admin.create_account(actor, "alex@example.invalid", "Alex Beispiel")
    member = admin.add_member(actor, tenant.id, user.id, (tenant.id + ":member",))
    profiles = ProfileService(runtime)
    registry = ExtensionRegistry()
    settings = SettingsService(runtime, registry)
    credentials = CredentialsService(runtime, password_policy)
    workspace = Workspace(profiles, settings, admin, credentials, timedelta(hours=1))
    return SimpleNamespace(
        repo=repo,
        runtime=runtime,
        now=now,
        admin=admin,
        actor=actor,
        tenant=tenant,
        user=user,
        member=member,
        user_actor=Actor(user.id, 1),
        profiles=profiles,
        registry=registry,
        settings=settings,
        credentials=credentials,
        workspace=workspace,
    )
