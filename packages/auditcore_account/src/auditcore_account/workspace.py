"""Gemeinsamer Formularadapter. Host bindet ihn an authentifizierte HTTP-Routen."""

from dataclasses import dataclass
from datetime import timedelta
from typing import Literal

from .admin import AdminService
from .credentials import CredentialsService
from .errors import AccountError, require
from .forms import Document, Item, branding_fields, document, field, schema_fields, welcome_fields
from .models import Actor, IssuedGrant, Kind
from .permissions import authenticated, permissions
from .profiles import ProfileService
from .runtime import revision
from .schema import MEMBERSHIP, PROFILE, TENANT
from .settings import SettingsService
from .workspace_access import AccessForms
from .workspace_admin import AdminForms


@dataclass(frozen=True)
class WorkspaceResult:
    document: Document
    actor: Actor
    delivery: IssuedGrant | None = None
    reauthenticate: bool = False


class Workspace:
    def __init__(
        self,
        profiles: ProfileService,
        settings: SettingsService,
        admin: AdminService,
        credentials: CredentialsService,
        access_lifetime: timedelta,
    ) -> None:
        self.profiles, self.settings, self.admin, self.credentials = (
            profiles,
            settings,
            admin,
            credentials,
        )
        self.runtime = profiles.runtime
        self.forms = AdminForms(admin)
        self.access = AccessForms(credentials, access_lifetime)

    def list(self, actor: Actor, tenant: str = "") -> list[Item]:
        with self.runtime.repository.transaction() as state:
            account = authenticated(state, actor, password_change=True)
            if account.must_change_password:
                return [Item(id="security", label="Startpasswort ändern", group="Mein Konto")]
            items = [
                Item(id="profile", label="Persönliche Angaben", group="Mein Konto"),
                Item(id="security", label="Passwort ändern", group="Mein Konto"),
            ]
            if tenant:
                rights = permissions(state, actor, tenant)
                require("tenant.read" in rights, "forbidden", "Mandant nicht zugänglich.")
                items += [
                    Item(id="tenant", label="Stammdaten", group="Mandant"),
                    Item(id="branding", label="Corporate Design", group="Mandant"),
                    Item(id="welcome", label="Begrüßung", group="Mandant"),
                ]
                if any(
                    m.account_id == actor.account_id and m.tenant_id == tenant and m.active
                    for m in state.memberships.values()
                ):
                    items.insert(
                        1, Item(id="contact", label="Funktion und Kontakt", group="Mein Konto")
                    )
                items += [
                    Item(id=e.id, label=e.title, group="Fachdaten")
                    for e in self.settings.extensions.list()
                    if e.read_permission in rights
                ]
            if account.platform_admin:
                items += [
                    Item(id=f"access/{a.id}", label=a.fields["display_name"], group="Zugänge")
                    for a in state.accounts.values()
                ]
        return items + self.forms.items(actor, tenant)

    def _target(self, actor: Actor, tenant: str, key: str) -> tuple[Kind, str]:
        if key == "profile":
            return "account", actor.account_id
        if key == "tenant":
            return "tenant", tenant
        with self.runtime.repository.transaction() as state:
            authenticated(state, actor)
            member = next(
                (
                    m
                    for m in state.memberships.values()
                    if m.account_id == actor.account_id and m.tenant_id == tenant and m.active
                ),
                None,
            )
            require(member is not None, "forbidden", "Mitgliedschaft nicht verfügbar.")
            assert member is not None
            return "membership", member.id

    def read(self, actor: Actor, key: str, tenant: str = "") -> Document:
        if key.startswith("access/"):
            return self.access.read(actor, key)
        if key == "security":
            with self.runtime.repository.transaction() as state:
                account = authenticated(state, actor, password_change=True)
                fields = [
                    field("current", "Aktuelles Passwort", "password", True),
                    field("new", "Neues Passwort", "password", True),
                    field("confirmation", "Neues Passwort wiederholen", "password", True),
                ]
                for entry in fields:
                    entry["autocomplete"] = (
                        "current-password" if entry["id"] == "current" else "new-password"
                    )
                return document(
                    key,
                    "Passwort ändern",
                    "security",
                    fields,
                    {},
                    account.revision,
                    not account.external,
                    "Nach dem Wechsel werden bisherige Sitzungen ungültig.",
                )
        if key in {"profile", "tenant", "contact"}:
            kind, target = self._target(actor, tenant, key)
            view = self.profiles.read(actor, kind, target)
            schemas = {"profile": PROFILE, "tenant": TENANT, "contact": MEMBERSHIP}
            fields = schema_fields(schemas[key], view.editable)
            values = dict(view.fields)
            if key != "contact":
                fields.insert(
                    0,
                    field(
                        "image_id", "Profilbild" if key == "profile" else "Mandantenbild", "image"
                    ),
                )
                values["image_id"] = view.image_id
            return document(
                key,
                {
                    "profile": "Persönliche Angaben",
                    "tenant": "Mandantenstammdaten",
                    "contact": "Funktion und Kontakt",
                }[key],
                "profile",
                fields,
                values,
                view.revision,
                bool(view.editable),
            )
        if key in {"branding", "welcome"} or "." in key:
            return self._settings(actor, tenant, key)
        return self.forms.read(actor, tenant, key)

    def _settings(self, actor: Actor, tenant: str, key: str) -> Document:
        result = self.settings.read(actor, tenant, key)
        if key == "branding":
            fields, title, permission = (
                branding_fields(self.settings.fonts),
                "Corporate Design",
                "branding.update",
            )
        elif key == "welcome":
            fields, title, permission = welcome_fields(), "Begrüßung", "welcome.update"
        else:
            extension = self.settings.extensions.get(key)
            fields = schema_fields(extension.fields, tuple(f.id for f in extension.fields))
            title, permission = extension.title, extension.write_permission
        with self.runtime.repository.transaction() as state:
            editable = permission in permissions(state, actor, tenant)
        kind: Literal["branding", "welcome", "extension"] = (
            "branding" if key == "branding" else "welcome" if key == "welcome" else "extension"
        )
        return document(key, title, kind, fields, result.fields, result.revision, editable)

    def save(
        self, actor: Actor, key: str, expected: int, values: dict[str, str], tenant: str = ""
    ) -> WorkspaceResult:
        """Host muss den zurückgegebenen Actor nach Passwortwechsel in die Session übernehmen."""
        current = self.read(actor, key, tenant)
        revision(current["revision"], expected)
        require(current["editable"], "forbidden", "Formular nicht bearbeitbar.")
        allowed = {f["id"] for f in current["fields"] if not f["readonly"]}
        require(set(values) <= allowed, "unknown_field", "Feld nicht bearbeitbar.")
        delivery = None
        if key.startswith("access/"):
            delivery = self.access.save(actor, key, expected, values)
        elif key == "security":
            require(
                values.get("new") == values.get("confirmation"),
                "invalid",
                "Passwörter stimmen nicht überein.",
            )
            actor = self.credentials.change(actor, values.get("current", ""), values.get("new", ""))
        elif key in {"profile", "tenant", "contact"}:
            kind, target = self._target(actor, tenant, key)
            self.profiles.update(
                actor,
                kind,
                target,
                expected,
                {k: v for k, v in values.items() if k != "image_id"},
                image_id=values.get("image_id"),
            )
        elif key in {"branding", "welcome"} or "." in key:
            version = (
                1 if key in {"branding", "welcome"} else self.settings.extensions.get(key).version
            )
            self.settings.save(actor, tenant, key, expected, version, values)
        else:
            self.forms.save(actor, tenant, key, expected, values)
        if key == "status/" + actor.account_id:
            return WorkspaceResult(
                document(
                    key,
                    "Kontostatus geändert",
                    "admin",
                    [],
                    {},
                    editable=False,
                    description="Bitte erneut anmelden.",
                ),
                actor,
                reauthenticate=True,
            )
        return self._after_save(actor, key, tenant, delivery)

    def _after_save(
        self, actor: Actor, key: str, tenant: str, delivery: IssuedGrant | None
    ) -> WorkspaceResult:
        try:
            return WorkspaceResult(self.read(actor, key, tenant), actor, delivery)
        except AccountError as error:
            if error.code not in {"forbidden", "unauthorized", "password_change_required"}:
                raise
            result = document(
                key,
                "Änderungen gespeichert",
                "admin",
                [],
                {},
                editable=False,
                description="Die Zugriffsrechte haben sich geändert. Bereich neu öffnen.",
            )
            return WorkspaceResult(
                result, actor, delivery, reauthenticate=error.code != "forbidden"
            )
