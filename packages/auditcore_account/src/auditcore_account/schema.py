"""Explizite Formularfelder und versionierte, typisierte Erweiterungsregistrierung."""

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass

from .errors import AccountError, require


@dataclass(frozen=True)
class Field:
    id: str
    label: str
    required: bool = False
    kind: str = "text"
    max_length: int = 500


PROFILE = (
    Field("display_name", "Anzeigename", True),
    Field("salutation", "Anrede"),
    Field("title", "Titel"),
    Field("given_name", "Vorname"),
    Field("family_name", "Nachname"),
)
TENANT = (
    Field("official_name", "Offizieller Name", True),
    Field("display_name", "Anzeigename", True),
    Field("short_name", "Kurzname"),
    Field("department", "Organisationseinheit"),
    Field("street", "Straße"),
    Field("house_number", "Hausnummer"),
    Field("address_extra", "Adresszusatz"),
    Field("postal_code", "Postleitzahl"),
    Field("city", "Ort"),
    Field("country", "Land"),
    Field("email", "E-Mail", kind="email"),
    Field("phone", "Telefon"),
    Field("website", "Website", kind="url"),
    Field("contact_name", "Ansprechperson"),
    Field("contact_function", "Funktion der Ansprechperson"),
)
MEMBERSHIP = (
    Field("function", "Funktion / Dienststellung"),
    Field("department", "Organisationseinheit"),
    Field("staff_code", "Bearbeiterkürzel"),
    Field("unit_code", "Stellenkürzel"),
    Field("email", "Dienstliche E-Mail", kind="email"),
    Field("phone", "Telefon"),
    Field("mobile", "Mobiltelefon"),
)
CONTACT_FIELDS = frozenset({"email", "phone", "mobile"})


@dataclass(frozen=True)
class Extension:
    id: str
    version: int
    title: str
    fields: tuple[Field, ...]
    read_permission: str
    write_permission: str
    validate: Callable[[Mapping[str, str]], None]


def validate_fields(fields: tuple[Field, ...], values: Mapping[str, str]) -> dict[str, str]:
    known = {f.id: f for f in fields}
    require(not set(values) - set(known), "unknown_field", "Unbekanntes Feld.")
    result: dict[str, str] = {}
    for key, value in values.items():
        require(isinstance(value, str), "invalid", "Text erwartet.", key)
        spec = known[key]
        text = value.strip()
        require(len(text) <= spec.max_length, "invalid", "Der Wert ist zu lang.", key)
        if text and spec.kind == "email":
            require(
                bool(re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", text)),
                "invalid",
                "Bitte eine gültige E-Mail-Adresse eingeben.",
                key,
            )
        if text and spec.kind == "url":
            require(text.startswith("https://"), "invalid", "Eine HTTPS-Adresse eingeben.", key)
        result[key] = text
    for spec in fields:
        require(
            not spec.required or bool(result.get(spec.id)),
            "required",
            "Dieses Feld ist erforderlich.",
            spec.id,
        )
    return result


def patch_fields(
    fields: tuple[Field, ...], current: Mapping[str, str], patch: Mapping[str, str | None]
) -> dict[str, str]:
    require(not set(patch) - {f.id for f in fields}, "unknown_field", "Unbekanntes Feld.")
    return validate_fields(
        fields, dict(current) | {k: "" if v is None else v for k, v in patch.items()}
    )


class ExtensionRegistry:
    def __init__(self) -> None:
        self._items: dict[str, Extension] = {}

    def register(self, extension: Extension) -> None:
        require(
            bool(re.fullmatch(r"[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*", extension.id)),
            "invalid",
            "Erweiterung braucht einen Namensraum.",
        )
        require(
            extension.id not in self._items and extension.version > 0,
            "conflict",
            "Erweiterung bereits registriert oder Version ungültig.",
        )
        require(
            len({f.id for f in extension.fields}) == len(extension.fields),
            "invalid",
            "Doppelte Feldkennung.",
        )
        self._items[extension.id] = extension

    def get(self, name: str) -> Extension:
        if name not in self._items:
            raise AccountError("unsupported_extension", "Erweiterung nicht installiert.")
        return self._items[name]

    def list(self) -> tuple[Extension, ...]:
        return tuple(self._items.values())
