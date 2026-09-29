"""Typisierte Konten, Mandanten und Mitgliedschaften; getrennte Zuständigkeiten."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

Kind = Literal["account", "tenant", "membership", "branding", "welcome", "extension"]


@dataclass(frozen=True)
class Actor:
    """Vom Host authentifizierte Identität und serverseitig geprüfte Sitzungsrevision."""

    account_id: str
    session_revision: int


@dataclass
class Account:
    id: str
    login: str
    fields: dict[str, str]
    active: bool = True
    external: bool = False
    platform_admin: bool = False
    revision: int = 1
    session_revision: int = 1
    password_hash: str = field(default="", repr=False)
    must_change_password: bool = False
    temporary_until: datetime | None = None
    image_id: str = ""


@dataclass
class Tenant:
    id: str
    slug: str
    fields: dict[str, str]
    status: Literal["setup", "active", "inactive"] = "setup"
    revision: int = 1
    image_id: str = ""


@dataclass
class Membership:
    id: str
    account_id: str
    tenant_id: str
    role_ids: tuple[str, ...]
    fields: dict[str, str] = field(default_factory=dict)
    active: bool = True
    revision: int = 1
    welcome_seen: bool = False


@dataclass
class Role:
    id: str
    tenant_id: str
    name: str
    permissions: frozenset[str]
    revision: int = 1
    system: bool = False


@dataclass
class Settings:
    tenant_id: str
    section: str
    version: int
    fields: dict[str, str]
    revision: int = 1


@dataclass(frozen=True)
class ProfileView:
    id: str
    kind: Kind
    tenant_id: str
    revision: int
    fields: dict[str, str]
    editable: tuple[str, ...]
    image_id: str = ""


@dataclass(frozen=True)
class Event:
    actor_id: str
    tenant_id: str
    operation: str
    target_id: str
    fields: tuple[str, ...]
    at: datetime


@dataclass
class Grant:
    digest: str
    account_id: str
    issuer_id: str
    tenant_id: str
    purpose: Literal["invite", "reset"]
    expires_at: datetime
    session_revision: int
    welcome_revision: int
    welcome_text: str
    message: str
    used: bool = False


@dataclass(frozen=True)
class IssuedGrant:
    """Nur zur unmittelbaren Übergabe an einen Versandadapter; niemals protokollieren."""

    token: str = field(repr=False)
    expires_at: datetime
    account_id: str
    welcome_text: str
    message: str


@dataclass
class Asset:
    id: str
    owner_id: str
    tenant_id: str
    content: bytes = field(repr=False)
    preview: bytes = field(repr=False)
    media_type: str
    expires_at: datetime
    attached: bool = False
