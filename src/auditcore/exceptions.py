"""Fachliche Fehler / Explicit domain failures."""


class AuditCoreError(Exception):
    """Basisfehler / Base error for callers to handle explicitly."""


class MigrationBlocked(AuditCoreError):
    """Migration gesperrt / Behavior or evidence prevents migration."""


class InvalidTransition(AuditCoreError):
    """Ungültiger Übergang / Workflow transition is not permitted."""
