"""Anlage, Sperren, Mitgliedschaften und delegierbare Rollen."""

from collections.abc import Mapping
from copy import deepcopy
from uuid import uuid4

from .errors import require
from .models import Account, Actor, Membership, Role, Tenant
from .permissions import (
    ADMIN,
    authenticated,
    authorize,
    ensure_administrator,
    permissions,
    platform,
    seed_roles,
)
from .repository import State
from .runtime import Runtime, revision
from .schema import PROFILE, TENANT, validate_fields


class AdminService:
    def __init__(self, runtime: Runtime, extra_permissions: frozenset[str] = frozenset()) -> None:
        self.runtime = runtime
        self.permission_catalog = ADMIN | extra_permissions

    def bootstrap(self, login: str, display_name: str) -> Account:
        """Expliziter Host-Aufruf für den ersten Admin, nicht als öffentliche Route anbieten."""
        with self.runtime.repository.transaction() as state:
            require(not state.accounts, "conflict", "Ersteinrichtung bereits abgeschlossen.")
            account = self._account(login, display_name, False)
            account.platform_admin = True
            state.accounts[account.id] = account
            return deepcopy(account)

    @staticmethod
    def _account(login: str, display_name: str, external: bool) -> Account:
        require(
            bool(login.strip()) and len(login) <= 255, "invalid", "Anmeldekennung erforderlich."
        )
        fields = validate_fields(PROFILE, {"display_name": display_name})
        return Account(uuid4().hex, login.strip().casefold(), fields, external=external)

    def create_account(
        self, actor: Actor, login: str, display_name: str, *, external: bool = False
    ) -> Account:
        with self.runtime.repository.transaction() as state:
            platform(state, actor)
            account = self._account(login, display_name, external)
            require(
                not any(a.login == account.login for a in state.accounts.values()),
                "conflict",
                "Anmeldekennung bereits vergeben.",
                "login",
            )
            state.accounts[account.id] = account
            self.runtime.event(state, actor, "account.create", account.id)
            return deepcopy(account)

    def create_tenant(self, actor: Actor, slug: str, fields: Mapping[str, str]) -> Tenant:
        import re

        with self.runtime.repository.transaction() as state:
            platform(state, actor)
            require(
                bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug)),
                "invalid",
                "Kennung: Kleinbuchstaben, Ziffern und Bindestriche.",
                "slug",
            )
            require(
                not any(t.slug == slug for t in state.tenants.values()),
                "conflict",
                "Mandantenkennung bereits vergeben.",
                "slug",
            )
            tenant = Tenant(uuid4().hex, slug, validate_fields(TENANT, fields))
            state.tenants[tenant.id] = tenant
            seed_roles(state, tenant.id)
            self.runtime.event(state, actor, "tenant.create", tenant.id, tenant.id)
            return deepcopy(tenant)

    def set_tenant_active(self, actor: Actor, tenant_id: str, expected: int, active: bool) -> None:
        with self.runtime.repository.transaction() as state:
            platform(state, actor)
            require(tenant_id in state.tenants, "not_found", "Mandant nicht gefunden.")
            tenant = state.tenants[tenant_id]
            revision(tenant.revision, expected)
            ensure_administrator(state, tenant_id)
            tenant.status = "active" if active else "inactive"
            tenant.revision += 1
            self.runtime.event(state, actor, "tenant.status", tenant_id, tenant_id)

    def add_member(
        self, actor: Actor, tenant_id: str, account_id: str, roles: tuple[str, ...]
    ) -> Membership:
        with self.runtime.repository.transaction() as state:
            authorize(state, actor, tenant_id, "membership.invite")
            require(account_id in state.accounts, "not_found", "Konto nicht verfügbar.")
            self._roles(state, actor, tenant_id, roles)
            require(
                not any(
                    m.account_id == account_id and m.tenant_id == tenant_id
                    for m in state.memberships.values()
                ),
                "conflict",
                "Bereits Mitglied.",
            )
            member = Membership(uuid4().hex, account_id, tenant_id, roles)
            state.memberships[member.id] = member
            self.runtime.event(state, actor, "membership.create", member.id, tenant_id)
            return deepcopy(member)

    def _roles(self, state: State, actor: Actor, tenant: str, roles: tuple[str, ...]) -> None:
        authorize(state, actor, tenant, "role.assign")
        grantable = (
            self.permission_catalog
            if authenticated(state, actor).platform_admin
            else permissions(state, actor, tenant)
        )
        for role_id in roles:
            role = state.roles.get(role_id)
            require(
                role is not None and role.tenant_id == tenant,
                "forbidden",
                "Rolle gehört nicht zum Mandanten.",
            )
            assert role is not None
            require(role.permissions <= grantable, "forbidden", "Rolle nicht delegierbar.")

    def update_member(
        self, actor: Actor, member_id: str, expected: int, roles: tuple[str, ...], active: bool
    ) -> Membership:
        with self.runtime.repository.transaction() as state:
            require(member_id in state.memberships, "forbidden", "Mitgliedschaft nicht verfügbar.")
            member = state.memberships[member_id]
            authorize(state, actor, member.tenant_id, "membership.update")
            self._roles(state, actor, member.tenant_id, roles)
            revision(member.revision, expected)
            member.role_ids, member.active = roles, active
            member.revision += 1
            ensure_administrator(state, member.tenant_id)
            self.runtime.event(state, actor, "membership.update", member.id, member.tenant_id)
            return deepcopy(member)

    def save_role(
        self,
        actor: Actor,
        tenant_id: str,
        name: str,
        rights: frozenset[str],
        *,
        role_id: str = "",
        expected: int = 0,
    ) -> Role:
        with self.runtime.repository.transaction() as state:
            authorize(state, actor, tenant_id, "role.create")
            require(bool(name.strip()), "required", "Rollenname erforderlich.", "name")
            require(rights <= self.permission_catalog, "invalid", "Unbekannte Berechtigung.")
            grantable = (
                self.permission_catalog
                if authenticated(state, actor).platform_admin
                else permissions(state, actor, tenant_id)
            )
            require(rights <= grantable, "forbidden", "Rechte nicht delegierbar.")
            current = state.roles.get(role_id)
            if role_id:
                require(
                    current is not None and current.tenant_id == tenant_id,
                    "forbidden",
                    "Rolle nicht verfügbar.",
                )
                assert current is not None
                require(not current.system, "forbidden", "Systemrolle ist geschützt.")
                revision(current.revision, expected)
            result = Role(
                role_id or uuid4().hex,
                tenant_id,
                name.strip(),
                rights,
                (current.revision + 1) if current else 1,
            )
            state.roles[result.id] = result
            ensure_administrator(state, tenant_id)
            self.runtime.event(state, actor, "role.save", result.id, tenant_id)
            return deepcopy(result)

    def suspend_account(self, actor: Actor, account_id: str, expected: int) -> None:
        with self.runtime.repository.transaction() as state:
            platform(state, actor)
            require(account_id in state.accounts, "not_found", "Konto nicht verfügbar.")
            account = state.accounts[account_id]
            revision(account.revision, expected)
            account.active = False
            account.revision += 1
            account.session_revision += 1
            ensure_administrator(state)
            self.runtime.event(state, actor, "account.suspend", account_id)

    def list_tenants(self, actor: Actor) -> tuple[Tenant, ...]:
        with self.runtime.repository.transaction() as state:
            account = authenticated(state, actor)
            ids = {
                m.tenant_id
                for m in state.memberships.values()
                if m.account_id == account.id and m.active
            }
            return tuple(
                deepcopy(t)
                for t in state.tenants.values()
                if account.platform_admin or (t.id in ids and t.status == "active")
            )

    def set_account_access(
        self, actor: Actor, target: str, expected: int, *, active: bool, platform_admin: bool
    ) -> None:
        """Plattformstatus explizit ändern und dabei bestehende Sessions widerrufen."""
        with self.runtime.repository.transaction() as state:
            platform(state, actor)
            account = state.accounts.get(target)
            require(account is not None, "not_found", "Konto nicht verfügbar.")
            assert account is not None
            revision(account.revision, expected)
            account.active, account.platform_admin = active, platform_admin
            account.revision += 1
            account.session_revision += 1
            ensure_administrator(state)
            self.runtime.event(
                state, actor, "account.access", target, fields=("active", "platform_admin")
            )
