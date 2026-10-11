"""Server-side permission check shared by the services of this package."""

from __future__ import annotations

from .errors import AuthorizationError
from .model import Actor, Permission
from .ports import Authorizer


def require_permission(
    authorizer: Authorizer, actor: Actor, permission: Permission, tenant_id: str
) -> None:
    """Raise ``AuthorizationError`` unless the actor may act in the tenant.

    Administration rights do not imply subject-matter decisions: only the
    named permission counts.
    """
    if not isinstance(actor, Actor) or not actor.id:
        raise AuthorizationError("Ohne zugeordnete Person ist keine Bearbeitung möglich.")
    if not authorizer.authorize(actor, permission, tenant_id):
        raise AuthorizationError(f"Keine Berechtigung für {permission.value}.")
