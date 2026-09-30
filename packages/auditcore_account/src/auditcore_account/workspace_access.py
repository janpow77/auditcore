"""Zugangsformulare geben Versandaufträge ausschließlich an den vertrauenswürdigen Host zurück."""

from datetime import timedelta

from .credentials import CredentialsService
from .errors import require
from .forms import Document, Option, choices, document, field
from .invitations import InvitationService
from .models import Actor, IssuedGrant
from .permissions import platform


class AccessForms:
    def __init__(self, credentials: CredentialsService, lifetime: timedelta) -> None:
        self.credentials = credentials
        self.invitations = InvitationService(credentials)
        self.runtime = credentials.runtime
        self.lifetime = lifetime

    def read(self, actor: Actor, key: str) -> Document:
        with self.runtime.repository.transaction() as state:
            platform(state, actor)
            require(key.startswith("access/"), "not_found", "Zugang nicht verfügbar.")
            account = state.accounts.get(key.removeprefix("access/"))
            require(account is not None, "not_found", "Konto nicht verfügbar.")
            assert account is not None
            tenants = [
                Option(value=m.tenant_id, label=state.tenants[m.tenant_id].fields["display_name"])
                for m in state.memberships.values()
                if m.account_id == account.id and m.active
            ]
            return document(
                key,
                "Zugang: " + account.fields["display_name"],
                "admin",
                [
                    choices(
                        "action",
                        "Vorgang",
                        [
                            Option(value="invite", label="Einladung"),
                            Option(value="reset", label="Passwort zurücksetzen"),
                            Option(value="provision", label="Startpasswort zuweisen"),
                        ],
                    ),
                    choices("tenant", "Mandant für Einladung", tenants),
                    field("message", "Persönlicher Zusatz zur Einladung", "textarea"),
                    field("password", "Startpasswort (nur bei Zuweisung)", "password"),
                ],
                {},
                account.revision,
                account.active and not account.external,
                "Der Versandanschluss der Anwendung stellt Einladungen und Reset-Links zu.",
                "Zugang bereitstellen",
            )

    def save(
        self, actor: Actor, key: str, expected: int, values: dict[str, str]
    ) -> IssuedGrant | None:
        target = key.removeprefix("access/")
        action = values.get("action")
        if action == "provision":
            self.credentials.provision(
                actor,
                target,
                values.get("password", ""),
                self.lifetime,
                expected_revision=expected,
            )
            return None
        require(action in {"invite", "reset"}, "invalid", "Vorgang erforderlich.")
        return self.invitations.issue(
            actor,
            target,
            values.get("tenant", ""),
            self.lifetime,
            purpose="reset" if action == "reset" else "invite",
            message=values.get("message", ""),
            expected_revision=expected,
        )
