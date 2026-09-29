"""Versionierte Mandanteneinstellungen und unabhängige Fach-Erweiterungen."""

from collections.abc import Mapping
from copy import deepcopy

from .branding import DEFAULT_BRANDING, FONTS, Font, validate_branding
from .errors import require
from .models import Actor, Settings
from .permissions import authorize
from .repository import State
from .runtime import Runtime, revision
from .schema import ExtensionRegistry, validate_fields
from .welcome import DEFAULT_WELCOME, validate_welcome


class SettingsService:
    def __init__(
        self,
        runtime: Runtime,
        extensions: ExtensionRegistry | None = None,
        fonts: tuple[Font, ...] = FONTS,
    ) -> None:
        self.runtime = runtime
        self.extensions = extensions or ExtensionRegistry()
        self.fonts = fonts

    def _permission(self, section: str, write: bool) -> str:
        if section in {"branding", "welcome"}:
            return f"{section}.update" if write else "tenant.read"
        extension = self.extensions.get(section)
        return extension.write_permission if write else extension.read_permission

    def read(self, actor: Actor, tenant_id: str, section: str) -> Settings:
        with self.runtime.repository.transaction() as state:
            authorize(state, actor, tenant_id, self._permission(section, False))
            existing = state.settings.get((tenant_id, section))
            if existing:
                return deepcopy(existing)
            defaults = {"branding": DEFAULT_BRANDING, "welcome": DEFAULT_WELCOME}
            version = 1 if section in defaults else self.extensions.get(section).version
            return Settings(
                tenant_id, section, version, dict(defaults.get(section, {})), revision=0
            )

    def save(
        self,
        actor: Actor,
        tenant_id: str,
        section: str,
        expected: int,
        version: int,
        fields: Mapping[str, str],
    ) -> Settings:
        with self.runtime.repository.transaction() as state:
            authorize(state, actor, tenant_id, self._permission(section, True))
            current = state.settings.get((tenant_id, section))
            revision(current.revision if current else 0, expected)
            values = self._validate(section, version, fields)
            if current:
                require(current.version == version, "schema_version", "Migration erforderlich.")
            if section == "branding":
                self._logos(state, actor, tenant_id, values)
            result = Settings(tenant_id, section, version, values, expected + 1)
            state.settings[(tenant_id, section)] = result
            self.runtime.event(
                state, actor, "settings.save", section, tenant_id, tuple(sorted(fields))
            )
            return deepcopy(result)

    def _validate(self, section: str, version: int, fields: Mapping[str, str]) -> dict[str, str]:
        if section in {"branding", "welcome"}:
            require(version == 1, "schema_version", "Schema nicht unterstützt.")
            return (
                validate_branding(fields, self.fonts)
                if section == "branding"
                else validate_welcome(fields)
            )
        extension = self.extensions.get(section)
        require(version == extension.version, "schema_version", "Migration erforderlich.")
        result = validate_fields(extension.fields, fields)
        extension.validate(result)
        return result

    def _logos(self, state: State, actor: Actor, tenant: str, fields: Mapping[str, str]) -> None:
        for key in ("logo_light", "logo_dark", "logo_document"):
            asset_id = fields[key]
            if not asset_id:
                continue
            asset = state.assets.get(asset_id)
            require(
                asset is not None and asset.tenant_id == tenant,
                "invalid_asset",
                "Logo gehört nicht zum Mandanten.",
                key,
            )
            assert asset is not None
            require(
                asset.attached
                or (asset.owner_id == actor.account_id and asset.expires_at > self.runtime.now()),
                "expired",
                "Logoentwurf abgelaufen.",
            )
            asset.attached = True

    def acknowledge_welcome(self, actor: Actor, membership_id: str) -> None:
        with self.runtime.repository.transaction() as state:
            member = state.memberships.get(membership_id)
            require(
                member is not None and member.account_id == actor.account_id and member.active,
                "forbidden",
                "Mitgliedschaft nicht zugänglich.",
            )
            assert member is not None
            authorize(state, actor, member.tenant_id, "tenant.read")
            member.welcome_seen = True

    def first_visit_welcome(self, actor: Actor, tenant_id: str) -> str | None:
        from .welcome import render_welcome

        with self.runtime.repository.transaction() as state:
            authorize(state, actor, tenant_id, "tenant.read")
            member = next(
                (
                    m
                    for m in state.memberships.values()
                    if m.account_id == actor.account_id and m.tenant_id == tenant_id and m.active
                ),
                None,
            )
            if member is None or member.welcome_seen:
                return None
            settings = state.settings.get((tenant_id, "welcome"))
            values = settings.fields if settings else DEFAULT_WELCOME
            if values["on_first_visit"] != "true":
                return None
            return render_welcome(
                values["heading"] + "\n\n" + values["body"],
                {
                    "display_name": state.accounts[actor.account_id].fields.get("display_name", ""),
                    "tenant_name": state.tenants[tenant_id].fields.get("display_name", ""),
                    "contact_name": state.tenants[tenant_id].fields.get("contact_name", ""),
                },
            )
