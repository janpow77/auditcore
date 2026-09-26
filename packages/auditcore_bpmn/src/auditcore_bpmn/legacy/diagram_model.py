"""Diagramm-Infos aus einer Zeile des Altmodells ``BpmnDiagram`` (audit_designer).

Quelle: ``backend/app/modules/flowstat/models/bpmn_diagram.py`` (Blob
``b5c31a11``) und ``schemas/bpmn.py`` (Blob ``95aad5ca``). Die Spalten
``header_title``/``header_subtitle``/``header_color``/``header_text_color``,
``description``, ``process_owner``, ``process_type``, ``version`` und
``is_archived`` werden auf ``flowaudit:diagrammInfo`` abgebildet; die
Standardfarben des Altmodells (``#1976d2``/``#ffffff``) bleiben erhalten.
"""

from __future__ import annotations

from collections.abc import Mapping

from ..extensions import DiagramInfo

LEGACY_HEADER_COLOR = "#1976d2"
LEGACY_HEADER_TEXT_COLOR = "#ffffff"


def _text(value: object) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None


def diagram_info_from_legacy(row: Mapping[str, object], *, profile: str | None = None) -> DiagramInfo:
    """``DiagramInfo`` aus einer Altzeile (``dict`` oder ORM-Objekt über ``vars``).

    ``header_title`` hat Vorrang vor ``name``; archivierte Diagramme erhalten
    den Status ``archiviert``, alle anderen bleiben ohne Status (die
    Anwendung entscheidet, ob ``entwurf`` oder ``freigegeben`` zutrifft).
    """
    return DiagramInfo(
        profile=profile,
        title=_text(row.get("header_title")) or _text(row.get("name")),
        subtitle=_text(row.get("header_subtitle")),
        description=_text(row.get("description")),
        process_owner=_text(row.get("process_owner")),
        process_type=_text(row.get("process_type")),
        version=_text(row.get("version")),
        status="archiviert" if row.get("is_archived") else None,
        header_color=_text(row.get("header_color")) or LEGACY_HEADER_COLOR,
        header_text_color=_text(row.get("header_text_color")) or LEGACY_HEADER_TEXT_COLOR,
    )
