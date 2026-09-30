"""Einmalige, gehashte Einladungs-/Reset-Token mit unveränderlichem Text-Snapshot."""

from datetime import timedelta
from hashlib import sha256
from secrets import token_urlsafe
from typing import Literal

from .credentials import CredentialsService
from .errors import require
from .models import Actor, Grant, IssuedGrant
from .permissions import platform
from .repository import State
from .runtime import revision
from .welcome import DEFAULT_WELCOME, render_welcome


class InvitationService:
    def __init__(self, credentials: CredentialsService) -> None:
        self.credentials = credentials
        self.runtime = credentials.runtime

    def issue(
        self,
        actor: Actor,
        target: str,
        tenant_id: str,
        lifetime: timedelta,
        *,
        purpose: Literal["invite", "reset"] = "invite",
        message: str = "",
        expected_revision: int | None = None,
    ) -> IssuedGrant:
        """Globale Kennwörter dürfen nur Plattformadmins zurücksetzen, nie Mandantenadmins."""
        require(lifetime.total_seconds() > 0, "invalid", "Gültigkeitsdauer erforderlich.")
        require(len(message) <= 2000, "invalid", "Zusatznachricht zu lang.")
        with self.runtime.repository.transaction() as state:
            platform(state, actor)
            account = state.accounts.get(target)
            tenant = state.tenants.get(tenant_id)
            require(
                account is not None and tenant is not None, "not_found", "Einladung nicht möglich."
            )
            assert account is not None and tenant is not None
            if expected_revision is not None:
                revision(account.revision, expected_revision)
            require(
                account.active and not account.external, "forbidden", "Kein lokales aktives Konto."
            )
            require(
                purpose != "invite" or not account.password_hash,
                "conflict",
                "Bestehendes Konto benötigt keinen neuen Zugang.",
            )
            require(
                any(
                    m.account_id == target and m.tenant_id == tenant_id and m.active
                    for m in state.memberships.values()
                ),
                "forbidden",
                "Mitgliedschaft erforderlich.",
            )
            settings_revision, welcome = self._welcome(state, target, tenant_id)
            token = token_urlsafe(32)
            digest = sha256(token.encode()).hexdigest()
            expiry = self.runtime.now() + lifetime
            state.grants[digest] = Grant(
                digest,
                target,
                actor.account_id,
                tenant_id,
                purpose,
                expiry,
                account.session_revision,
                settings_revision,
                welcome,
                message,
            )
            self.runtime.event(state, actor, "invitation.issue", target, tenant_id)
            return IssuedGrant(token, expiry, target, welcome, message)

    def redeem(self, token: str, password: str) -> Actor:
        self.credentials.validate_password(password)
        with self.runtime.repository.transaction() as state:
            grant = state.grants.get(sha256(token.encode()).hexdigest())
            require(grant is not None and not grant.used, "invalid_token", "Link nicht gültig.")
            assert grant is not None
            require(grant.expires_at > self.runtime.now(), "expired", "Link abgelaufen.")
            account = state.accounts[grant.account_id]
            issuer = state.accounts[grant.issuer_id]
            require(issuer.active and issuer.platform_admin, "invalid_token", "Link widerrufen.")
            require(
                account.active
                and not account.external
                and account.session_revision == grant.session_revision,
                "invalid_token",
                "Link widerrufen.",
            )
            require(
                state.tenants[grant.tenant_id].status != "inactive"
                and any(
                    m.account_id == account.id and m.tenant_id == grant.tenant_id and m.active
                    for m in state.memberships.values()
                ),
                "invalid_token",
                "Mitgliedschaft nicht mehr aktiv.",
            )
            account.password_hash = self.credentials.hasher.hash(password)
            account.must_change_password = False
            account.temporary_until = None
            account.session_revision += 1
            account.revision += 1
            grant.used = True
            actor = Actor(account.id, account.session_revision)
            self.runtime.event(state, actor, "invitation.redeem", account.id, grant.tenant_id)
            return actor

    def _welcome(self, state: State, target: str, tenant_id: str) -> tuple[int, str]:
        account, tenant = state.accounts[target], state.tenants[tenant_id]
        settings = state.settings.get((tenant_id, "welcome"))
        fields = settings.fields if settings else DEFAULT_WELCOME
        welcome = (
            render_welcome(
                fields["heading"] + "\n\n" + fields["body"],
                {
                    "display_name": account.fields.get("display_name", ""),
                    "tenant_name": tenant.fields.get("display_name", ""),
                    "contact_name": tenant.fields.get("contact_name", ""),
                },
            )
            if fields.get("in_invitation") == "true"
            else ""
        )
        return settings.revision if settings else 0, welcome
