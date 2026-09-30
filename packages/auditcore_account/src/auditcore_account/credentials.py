"""Passwortwechsel und Sitzungswiderruf über auditcore_auth."""

from collections.abc import Callable
from datetime import timedelta

from auditcore_auth import PasswordHasher

from .errors import require
from .models import Actor
from .permissions import authenticated, platform
from .runtime import Runtime, revision


class CredentialsService:
    def __init__(
        self,
        runtime: Runtime,
        validate_password: Callable[[str], None],
        hasher: PasswordHasher | None = None,
    ) -> None:
        self.runtime = runtime
        self.validate_password = validate_password
        self.hasher = hasher or PasswordHasher()

    def login(self, login: str, password: str) -> Actor:
        """Host muss Rate-Limit, MFA und Session-Cookie ergänzen."""
        with self.runtime.repository.transaction() as state:
            account = next(
                (a for a in state.accounts.values() if a.login == login.strip().casefold()), None
            )
            valid = self.hasher.verify(password, account.password_hash if account else None)
            require(valid and account is not None, "unauthorized", "Anmeldung fehlgeschlagen.")
            assert account is not None
            require(
                account.active and not account.external, "unauthorized", "Anmeldung fehlgeschlagen."
            )
            require(
                account.temporary_until is None or account.temporary_until > self.runtime.now(),
                "expired",
                "Startpasswort abgelaufen.",
            )
            return Actor(account.id, account.session_revision)

    def change(self, actor: Actor, current: str, new: str) -> Actor:
        self.validate_password(new)
        with self.runtime.repository.transaction() as state:
            account = authenticated(state, actor, password_change=True)
            require(
                not account.external,
                "external_identity",
                "Passwort beim Identitätsanbieter ändern.",
            )
            require(
                account.temporary_until is None or account.temporary_until > self.runtime.now(),
                "expired",
                "Startpasswort abgelaufen.",
            )
            require(
                self.hasher.verify(current, account.password_hash),
                "unauthorized",
                "Aktuelles Passwort nicht bestätigt.",
            )
            require(current != new, "invalid", "Neues Passwort muss sich unterscheiden.")
            account.password_hash = self.hasher.hash(new)
            account.must_change_password = False
            account.temporary_until = None
            account.session_revision += 1
            account.revision += 1
            self.runtime.event(state, actor, "password.change", account.id)
            return Actor(account.id, account.session_revision)

    def provision(
        self,
        actor: Actor,
        target: str,
        password: str,
        lifetime: timedelta,
        expected_revision: int | None = None,
    ) -> None:
        """Plattform-Fallback; einmalige Übergabe, keine Rückgabe des Passworts."""
        self.validate_password(password)
        require(lifetime.total_seconds() > 0, "invalid", "Gültigkeitsdauer erforderlich.")
        with self.runtime.repository.transaction() as state:
            platform(state, actor)
            account = state.accounts.get(target)
            require(account is not None, "not_found", "Konto nicht verfügbar.")
            assert account is not None
            if expected_revision is not None:
                revision(account.revision, expected_revision)
            require(
                account.active and not account.external, "forbidden", "Kein lokales aktives Konto."
            )
            account.password_hash = self.hasher.hash(password)
            account.must_change_password = True
            account.temporary_until = self.runtime.now() + lifetime
            account.session_revision += 1
            account.revision += 1
            self.runtime.event(state, actor, "password.provision", target)
