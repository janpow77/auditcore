"""Begrüßung mit sicherer Platzhalterersetzung; kein ausführbarer Vorlagencode."""

import re
from collections.abc import Mapping
from html import escape

from .errors import require

DEFAULT_WELCOME = {
    "heading": "Willkommen",
    "body": "Guten Tag {{display_name}},\n\nwillkommen bei {{tenant_name}}.",
    "in_invitation": "true",
    "on_first_visit": "true",
}
TOKENS = frozenset({"display_name", "tenant_name", "contact_name"})
TOKEN = re.compile(r"{{\s*([^{}]+?)\s*}}")


def validate_welcome(values: Mapping[str, str]) -> dict[str, str]:
    require(not set(values) - set(DEFAULT_WELCOME), "unknown_field", "Unbekanntes Begrüßungsfeld.")
    result = DEFAULT_WELCOME | dict(values)
    require(bool(result["heading"].strip()), "required", "Überschrift erforderlich.", "heading")
    require(
        len(result["heading"]) <= 200 and len(result["body"]) <= 10000,
        "invalid",
        "Begrüßung ist zu lang.",
    )
    for field in ("heading", "body"):
        require(
            set(TOKEN.findall(result[field])) <= TOKENS,
            "invalid_placeholder",
            "Unbekannter Platzhalter.",
            field,
        )
    for field in ("in_invitation", "on_first_visit"):
        require(result[field] in {"true", "false"}, "invalid", "Ungültige Auswahl.", field)
    return result


def render_welcome(template: str, values: Mapping[str, str]) -> str:
    """Klartext; HTML-Renderer muss weiterhin escapen."""
    require(
        set(TOKEN.findall(template)) <= TOKENS, "invalid_placeholder", "Unbekannter Platzhalter."
    )
    return TOKEN.sub(
        lambda match: values.get(match.group(1), "") or "Ihr Organisationskontakt", template
    )


def welcome_html(text: str) -> str:
    """Bewusst eingeschränktes Markdown: Absätze, Listen, fett und kursiv; keine Links/HTML."""
    lines: list[str] = []
    for raw in text.splitlines():
        safe = escape(raw)
        safe = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", safe)
        safe = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", safe)
        lines.append(f"<p>• {safe[2:]}</p>" if safe.startswith("- ") else f"<p>{safe}</p>")
    return "".join(lines)
