"""Mandantengebundene Fähigkeiten; Plattformverwaltung gewährt keine Fachrechte."""

from .errors import require
from .models import Account, Actor, Role
from .repository import State

MEMBER = frozenset({"tenant.read"})
ADMIN = MEMBER | frozenset(
    {
        "tenant.update",
        "membership.read",
        "membership.invite",
        "membership.update",
        "role.read",
        "role.assign",
        "role.create",
        "branding.update",
        "welcome.update",
        "audit.read",
    }
)


def authenticated(state: State, actor: Actor, *, password_change: bool = False) -> Account:
    account = state.accounts.get(actor.account_id)
    require(account is not None, "unauthorized", "Anmeldung erforderlich.")
    assert account is not None
    require(
        account.active and account.session_revision == actor.session_revision,
        "unauthorized",
        "Die Sitzung ist nicht mehr gültig.",
    )
    require(
        password_change or not account.must_change_password,
        "password_change_required",
        "Bitte zuerst das Startpasswort ändern.",
    )
    return account


def platform(state: State, actor: Actor) -> Account:
    account = authenticated(state, actor)
    require(account.platform_admin, "forbidden", "Plattformberechtigung erforderlich.")
    return account


def permissions(state: State, actor: Actor, tenant_id: str) -> frozenset[str]:
    account = authenticated(state, actor)
    tenant = state.tenants.get(tenant_id)
    require(tenant is not None, "forbidden", "Mandant nicht zugänglich.")
    assert tenant is not None
    if account.platform_admin:
        return ADMIN
    require(tenant.status == "active", "forbidden", "Mandant nicht aktiv.")
    rights: set[str] = set()
    for member in state.memberships.values():
        if member.account_id != account.id or member.tenant_id != tenant_id or not member.active:
            continue
        for role_id in member.role_ids:
            role = state.roles.get(role_id)
            if role is not None and role.tenant_id == tenant_id:
                rights.update(role.permissions)
    return frozenset(rights)


def authorize(state: State, actor: Actor, tenant_id: str, permission: str) -> None:
    require(
        permission in permissions(state, actor, tenant_id),
        "forbidden",
        "Für diesen Vorgang fehlt die Berechtigung.",
    )


def seed_roles(state: State, tenant_id: str) -> None:
    for suffix, name, rights in (
        ("member", "Mitglied", MEMBER),
        ("admin", "Mandantenadministrator", ADMIN),
    ):
        role_id = f"{tenant_id}:{suffix}"
        state.roles[role_id] = Role(role_id, tenant_id, name, rights, system=True)


def ensure_administrator(state: State, tenant_id: str = "") -> None:
    if any(a.active and a.platform_admin for a in state.accounts.values()):
        return
    for member in state.memberships.values():
        account = state.accounts[member.account_id]
        if member.tenant_id != tenant_id or not member.active or not account.active:
            continue
        if any(state.roles[r].permissions >= ADMIN for r in member.role_ids):
            return
    require(
        False, "last_administrator", "Die letzte Administrationszuständigkeit bleibt erforderlich."
    )
