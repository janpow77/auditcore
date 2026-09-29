"""JSON-Vertrag des gemeinsamen Vue-/React-Formulars."""

from typing import Literal, NotRequired, TypedDict

from .branding import Font
from .schema import Field


class Option(TypedDict):
    value: str
    label: str


class FormField(TypedDict):
    id: str
    label: str
    type: str
    required: bool
    readonly: bool
    options: NotRequired[list[Option]]
    autocomplete: NotRequired[str]


class Document(TypedDict):
    id: str
    title: str
    description: str
    kind: Literal["profile", "branding", "welcome", "security", "admin", "extension"]
    revision: int
    fields: list[FormField]
    values: dict[str, str]
    editable: bool
    submitLabel: str


class Item(TypedDict):
    id: str
    label: str
    group: str


def field(
    key: str, label: str, kind: str = "text", required: bool = False, *, readonly: bool = False
) -> FormField:
    return FormField(id=key, label=label, type=kind, required=required, readonly=readonly)


def choices(key: str, label: str, options: list[Option]) -> FormField:
    result = field(key, label, "select", True)
    result["options"] = options
    return result


def schema_fields(schema: tuple[Field, ...], editable: tuple[str, ...]) -> list[FormField]:
    return [field(f.id, f.label, f.kind, f.required, readonly=f.id not in editable) for f in schema]


def branding_fields(fonts: tuple[Font, ...]) -> list[FormField]:
    options = [Option(value=f.id, label=f.label) for f in fonts]
    return [
        field("primary", "Primärfarbe", "color"),
        field("accent", "Akzentfarbe", "color"),
        field("text_on_primary", "Text auf Markenfarbe", "color"),
        choices("heading_font", "Überschriftenschrift", options),
        choices("body_font", "Textschrift", options),
        field("logo_light", "Logo auf hellem Hintergrund", "image"),
        field("logo_dark", "Logo auf dunklem Hintergrund", "image"),
        field("logo_document", "Dokumentlogo", "image"),
        field("document_header", "Dokumentkopf", "textarea"),
        field("document_footer", "Dokumentfuß", "textarea"),
    ]


def welcome_fields() -> list[FormField]:
    options = [Option(value="true", label="Ja"), Option(value="false", label="Nein")]
    return [
        field("heading", "Überschrift", required=True),
        field("body", "Begrüßungstext", "textarea"),
        choices("in_invitation", "In Einladungen verwenden", options),
        choices("on_first_visit", "Beim ersten Besuch anzeigen", options),
    ]


def document(
    key: str,
    title: str,
    kind: Literal["profile", "branding", "welcome", "security", "admin", "extension"],
    fields: list[FormField],
    values: dict[str, str],
    revision: int = 0,
    editable: bool = True,
    description: str = "",
    submit: str = "Änderungen speichern",
) -> Document:
    return Document(
        id=key,
        title=title,
        description=description,
        kind=kind,
        revision=revision,
        fields=fields,
        values=values,
        editable=editable,
        submitLabel=submit,
    )
