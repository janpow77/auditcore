"""Profilzugriff mit Feldrechten und atomarem Versionsvergleich."""

from collections.abc import Mapping
from copy import deepcopy

from .errors import require
from .models import Account, Actor, Kind, Membership, ProfileView, Tenant
from .permissions import authenticated, authorize, permissions
from .repository import State
from .runtime import Runtime, revision
from .schema import CONTACT_FIELDS, MEMBERSHIP, PROFILE, TENANT, Field, patch_fields


class ProfileService:
    def __init__(self, runtime: Runtime) -> None:
        self.runtime = runtime

    def read(self, actor: Actor, kind: Kind, target: str) -> ProfileView:
        with self.runtime.repository.transaction() as state:
            return self._view(state, actor, kind, target)

    def _view(self, state: State, actor: Actor, kind: Kind, target: str) -> ProfileView:
        account = authenticated(state, actor)
        if kind == "account":
            require(
                target == account.id or account.platform_admin,
                "forbidden",
                "Konto nicht zugänglich.",
            )
            record = state.accounts.get(target)
            require(record is not None, "not_found", "Konto nicht gefunden.")
            assert record is not None
            editable = () if record.external else tuple(f.id for f in PROFILE)
            return ProfileView(
                record.id, kind, "", record.revision, dict(record.fields), editable, record.image_id
            )
        if kind == "tenant":
            authorize(state, actor, target, "tenant.read")
            tenant = state.tenants[target]
            allowed = "tenant.update" in permissions(state, actor, target)
            return ProfileView(
                tenant.id,
                kind,
                tenant.id,
                tenant.revision,
                dict(tenant.fields),
                tuple(f.id for f in TENANT) if allowed else (),
                tenant.image_id,
            )
        require(kind == "membership", "invalid", "Profilart nicht unterstützt.")
        member = state.memberships.get(target)
        require(member is not None, "forbidden", "Mitgliedschaft nicht zugänglich.")
        assert member is not None
        rights = permissions(state, actor, member.tenant_id)
        require(
            (member.account_id == account.id and member.active) or "membership.read" in rights,
            "forbidden",
            "Mitgliedschaft nicht zugänglich.",
        )
        fields = tuple(f.id for f in MEMBERSHIP)
        editable = (
            fields
            if "membership.update" in rights
            else (tuple(sorted(CONTACT_FIELDS)) if member.account_id == account.id else ())
        )
        return ProfileView(
            member.id, kind, member.tenant_id, member.revision, dict(member.fields), editable
        )

    def update(
        self,
        actor: Actor,
        kind: Kind,
        target: str,
        expected_revision: int,
        patch: Mapping[str, str | None],
        *,
        image_id: str | None = None,
    ) -> ProfileView:
        with self.runtime.repository.transaction() as state:
            current = self._view(state, actor, kind, target)
            revision(current.revision, expected_revision)
            require(not set(patch) - set(current.editable), "forbidden", "Feld nicht bearbeitbar.")
            schemas: dict[Kind, tuple[Field, ...]] = {
                "account": PROFILE,
                "tenant": TENANT,
                "membership": MEMBERSHIP,
            }
            values = patch_fields(schemas[kind], current.fields, patch)
            record = self._record(state, kind, target)
            record.fields = values
            if image_id is not None:
                require(
                    kind in {"account", "tenant"} and bool(current.editable),
                    "forbidden",
                    "Bild nicht bearbeitbar.",
                )
                self._attach(state, actor, current.tenant_id, image_id)
                if kind == "account":
                    state.accounts[target].image_id = image_id
                elif kind == "tenant":
                    state.tenants[target].image_id = image_id
            record.revision += 1
            changed = tuple(sorted(patch)) + (("image_id",) if image_id is not None else ())
            self.runtime.event(state, actor, "profile.update", target, current.tenant_id, changed)
            return deepcopy(self._view(state, actor, kind, target))

    @staticmethod
    def _record(state: State, kind: Kind, target: str) -> Account | Membership | Tenant:
        record: Account | Membership | Tenant
        if kind == "account":
            record = state.accounts[target]
        elif kind == "tenant":
            record = state.tenants[target]
        else:
            record = state.memberships[target]
        return record

    def _attach(self, state: State, actor: Actor, tenant: str, image_id: str) -> None:
        if not image_id:
            return
        asset = state.assets.get(image_id)
        require(asset is not None, "invalid_asset", "Bild nicht verfügbar.")
        assert asset is not None
        require(
            asset.owner_id == actor.account_id and asset.tenant_id == tenant,
            "forbidden",
            "Bild gehört zu einem anderen Vorgang.",
        )
        require(
            asset.attached or asset.expires_at > self.runtime.now(),
            "expired",
            "Bildentwurf abgelaufen.",
        )
        asset.attached = True
