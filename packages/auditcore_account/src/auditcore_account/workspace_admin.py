"""Administrative Formulare; Rechte werden auch bei direktem Aufruf geprüft."""

from .admin import AdminService
from .errors import require
from .forms import Document, FormField, Item, Option, choices, document, field
from .models import Actor
from .permissions import authenticated, authorize, platform
from .repository import State
from .runtime import revision


class AdminForms:
    def __init__(self, admin: AdminService) -> None:
        self.admin = admin
        self.runtime = admin.runtime

    def items(self, actor: Actor, tenant: str) -> list[Item]:
        result: list[Item] = []
        with self.runtime.repository.transaction() as state:
            account = authenticated(state, actor)
            if account.platform_admin:
                result += [
                    Item(id="new-tenant", label="Mandant anlegen", group="Administration"),
                    Item(id="new-account", label="Nutzer anlegen", group="Administration"),
                ]
                result += [
                    Item(id=f"status/{a.id}", label=a.fields["display_name"], group="Kontostatus")
                    for a in state.accounts.values()
                ]
                result += [
                    Item(
                        id=f"tenant-status/{t.id}",
                        label=t.fields["display_name"],
                        group="Mandantenstatus",
                    )
                    for t in state.tenants.values()
                ]
            if not tenant:
                return result
            from .permissions import permissions

            rights = permissions(state, actor, tenant)
            if "membership.invite" in rights:
                result.append(
                    Item(id="new-member", label="Mitglied zuordnen", group="Administration")
                )
            if "role.read" in rights:
                result += [
                    Item(id=f"role/{r.id}", label=r.name, group="Rollen")
                    for r in state.roles.values()
                    if r.tenant_id == tenant
                ]
            if "role.create" in rights:
                result.append(Item(id="new-role", label="Rolle anlegen", group="Administration"))
            if "membership.read" in rights:
                for member in state.memberships.values():
                    if member.tenant_id == tenant:
                        name = state.accounts[member.account_id].fields["display_name"]
                        result.append(
                            Item(id=f"member/{member.id}", label=name, group="Nutzer und Rollen")
                        )
            return result

    def read(self, actor: Actor, tenant: str, key: str) -> Document:
        with self.runtime.repository.transaction() as state:
            if key.startswith("tenant-status/"):
                return self._tenant_status(state, actor, key)
            if key.startswith("role/"):
                return self._role(state, actor, tenant, key)
            if key.startswith("status/"):
                return self._status(state, actor, key)
            if key == "new-tenant":
                platform(state, actor)
                return document(
                    key,
                    "Mandant anlegen",
                    "admin",
                    [
                        field("slug", "Kennung", required=True),
                        field("official_name", "Offizieller Name", required=True),
                        field("display_name", "Anzeigename", required=True),
                    ],
                    {},
                    submit="Mandant anlegen",
                )
            if key == "new-account":
                platform(state, actor)
                return document(
                    key,
                    "Nutzer anlegen",
                    "admin",
                    [
                        field("login", "Anmeldekennung", required=True),
                        field("display_name", "Anzeigename", required=True),
                    ],
                    {},
                    submit="Nutzer anlegen",
                )
            if key == "new-member":
                authorize(state, actor, tenant, "membership.invite")
                roles = [
                    Option(value=r.id, label=r.name)
                    for r in state.roles.values()
                    if r.tenant_id == tenant
                ]
                return document(
                    key,
                    "Mitglied zuordnen",
                    "admin",
                    [
                        field("login", "Anmeldekennung des Kontos", required=True),
                        choices("role_id", "Rolle", roles),
                    ],
                    {},
                    submit="Mitglied zuordnen",
                )
            if key == "new-role":
                return self._new_role(state, actor, tenant, key)
            return self._member(state, actor, tenant, key)

    def _member(self, state: State, actor: Actor, tenant: str, key: str) -> Document:
        require(key.startswith("member/"), "not_found", "Formular nicht verfügbar.")
        member = state.memberships.get(key.removeprefix("member/"))
        require(
            member is not None and member.tenant_id == tenant,
            "forbidden",
            "Mitglied nicht verfügbar.",
        )
        assert member is not None
        authorize(state, actor, tenant, "membership.update")
        return document(
            key,
            "Mitgliedschaft und Rollen",
            "admin",
            [
                self._role_choices(state, tenant),
                choices(
                    "active",
                    "Mitgliedschaft aktiv",
                    [Option(value="true", label="Ja"), Option(value="false", label="Nein")],
                ),
            ],
            {"roles": "\n".join(member.role_ids), "active": str(member.active).lower()},
            member.revision,
        )

    def save(
        self, actor: Actor, tenant: str, key: str, expected: int, values: dict[str, str]
    ) -> None:
        current = self.read(actor, tenant, key)
        revision(current["revision"], expected)
        require(
            set(values) <= {f["id"] for f in current["fields"]},
            "unknown_field",
            "Unbekanntes Feld.",
        )
        if key.startswith("tenant-status/"):
            require(values.get("active") in {"true", "false"}, "invalid", "Status erforderlich.")
            self.admin.set_tenant_active(
                actor, key.removeprefix("tenant-status/"), expected, values["active"] == "true"
            )
        elif key.startswith("role/"):
            self.admin.save_role(
                actor,
                tenant,
                values.get("name", ""),
                frozenset(values.get("permissions", "").split()),
                role_id=key.removeprefix("role/"),
                expected=expected,
            )
        elif key.startswith("status/"):
            self._save_status(actor, key, expected, values)
        elif key == "new-tenant":
            self.admin.create_tenant(
                actor, values.get("slug", ""), {k: v for k, v in values.items() if k != "slug"}
            )
        elif key == "new-account":
            self.admin.create_account(
                actor, values.get("login", ""), values.get("display_name", "")
            )
        elif key == "new-member":
            self.admin.add_member(
                actor,
                tenant,
                self._account_id(actor, tenant, values.get("login", "")),
                (values.get("role_id", ""),),
            )
        elif key == "new-role":
            self.admin.save_role(
                actor,
                tenant,
                values.get("name", ""),
                frozenset(values.get("permissions", "").split()),
            )
        else:
            require(values.get("active") in {"true", "false"}, "invalid", "Status erforderlich.")
            self.admin.update_member(
                actor,
                key.removeprefix("member/"),
                expected,
                tuple(values.get("roles", "").split()),
                values["active"] == "true",
            )

    def _role_choices(self, state: State, tenant: str) -> FormField:
        result = choices(
            "roles",
            "Rollen",
            [
                Option(value=r.id, label=r.name)
                for r in state.roles.values()
                if r.tenant_id == tenant
            ],
        )
        result["type"] = "multiselect"
        return result

    def _permission_choices(self) -> FormField:
        result = choices(
            "permissions",
            "Berechtigungen",
            [Option(value=p, label=p) for p in sorted(self.admin.permission_catalog)],
        )
        result["type"] = "multiselect"
        return result

    def _account_id(self, actor: Actor, tenant: str, login: str) -> str:
        with self.runtime.repository.transaction() as state:
            authorize(state, actor, tenant, "membership.invite")
            account = next(
                (a for a in state.accounts.values() if a.login == login.strip().casefold()), None
            )
            require(
                account is not None,
                "not_found",
                "Konto nicht verfügbar; Plattformverwaltung kontaktieren.",
            )
            assert account is not None
            return account.id

    def _status(self, state: State, actor: Actor, key: str) -> Document:
        platform(state, actor)
        account = state.accounts.get(key.removeprefix("status/"))
        require(account is not None, "not_found", "Konto nicht verfügbar.")
        assert account is not None
        options = [Option(value="true", label="Ja"), Option(value="false", label="Nein")]
        return document(
            key,
            "Kontostatus: " + account.fields["display_name"],
            "admin",
            [
                choices("active", "Konto aktiv", options),
                choices("platform_admin", "Plattformverwaltung", options),
            ],
            {
                "active": str(account.active).lower(),
                "platform_admin": str(account.platform_admin).lower(),
            },
            account.revision,
            description="Änderungen widerrufen alle bestehenden Sitzungen dieses Kontos.",
        )

    def _new_role(self, state: State, actor: Actor, tenant: str, key: str) -> Document:
        authorize(state, actor, tenant, "role.create")
        return document(
            key,
            "Rolle anlegen",
            "admin",
            [
                field("name", "Rollenname", required=True),
                self._permission_choices(),
            ],
            {},
            description="Nur eigene, registrierte Berechtigungen sind delegierbar.",
            submit="Rolle anlegen",
        )

    def _tenant_status(self, state: State, actor: Actor, key: str) -> Document:
        platform(state, actor)
        tenant = state.tenants.get(key.removeprefix("tenant-status/"))
        require(tenant is not None, "not_found", "Mandant nicht verfügbar.")
        assert tenant is not None
        return document(
            key,
            "Mandantenstatus: " + tenant.fields["display_name"],
            "admin",
            [
                choices(
                    "active",
                    "Mandant aktiv",
                    [Option(value="true", label="Ja"), Option(value="false", label="Nein")],
                )
            ],
            {"active": str(tenant.status == "active").lower()},
            tenant.revision,
        )

    def _role(self, state: State, actor: Actor, tenant: str, key: str) -> Document:
        authorize(state, actor, tenant, "role.read")
        role = state.roles.get(key.removeprefix("role/"))
        require(
            role is not None and role.tenant_id == tenant, "forbidden", "Rolle nicht verfügbar."
        )
        assert role is not None
        from .permissions import permissions

        editable = not role.system and "role.create" in permissions(state, actor, tenant)
        return document(
            key,
            "Rolle: " + role.name,
            "admin",
            [field("name", "Rollenname", required=True), self._permission_choices()],
            {"name": role.name, "permissions": "\n".join(sorted(role.permissions))},
            role.revision,
            editable,
            "Systemrollen sind schreibgeschützt.",
        )

    def _save_status(self, actor: Actor, key: str, expected: int, values: dict[str, str]) -> None:
        require(
            values.get("active") in {"true", "false"}
            and values.get("platform_admin") in {"true", "false"},
            "invalid",
            "Status erforderlich.",
        )
        self.admin.set_account_access(
            actor,
            key.removeprefix("status/"),
            expected,
            active=values["active"] == "true",
            platform_admin=values["platform_admin"] == "true",
        )
