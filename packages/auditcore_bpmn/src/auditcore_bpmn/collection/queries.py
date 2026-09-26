"""Abfragen über eine Sammlung: Suche, Schlüssel, Übersicht, Verweise."""

from __future__ import annotations

from collections import Counter
from datetime import date

from ..errors import CollectionError
from ..vocabulary import DIAGRAM_STATUS
from .collection import DiagramCollection
from .model import KEY_KINDS, DiagramEntry, DiagramReference, GroupOverview


def _haystack(entry: DiagramEntry) -> str:
    info = entry.info
    parts = [entry.name]
    if info is not None:
        parts += [info.title or "", info.subtitle or "", info.description or "", " ".join(info.keywords)]
    return " ".join(part for part in parts if part).casefold()


def search(
    collection: DiagramCollection, term: str = "", *, status: str | None = None, tag: str | None = None
) -> list[DiagramEntry]:
    """Volltextsuche über Name, Titel, Untertitel, Beschreibung und Schlagwörter."""
    needle = term.strip().casefold()
    found = [
        entry
        for entry in collection.diagrams.values()
        if (status is None or entry.status == status)
        and (tag is None or tag in entry.tags)
        and needle in _haystack(entry)
    ]
    return sorted(found, key=lambda d: (d.name.casefold(), d.id))


def elements_by_key(collection: DiagramCollection, kind: str, value: str) -> list[tuple[str, str]]:
    """``(diagramm_id, element_id)`` aller Elemente mit einem fachlichen Schlüssel.

    ``kind``: ``ka``, ``bk``, ``prueffeld``, ``feststellung_ref``, ``register``,
    ``rolle`` oder ``kennzeichen``. Diagrammweite Angaben tragen die ID des
    Hauptelements. Verknüpfung nur über diese Schlüssel, nie über IDs fremder Systeme.
    """
    if kind not in KEY_KINDS:
        raise CollectionError(f"Unbekannte Schlüsselart „{kind}“ (zulässig: {', '.join(KEY_KINDS)}).")
    wanted = str(value).strip()
    return [
        (entry.id, element_id)
        for entry in sorted(collection.diagrams.values(), key=lambda d: d.id)
        for element_id in entry.excerpt.keys.get(kind, {}).get(wanted, [])
    ]


def _status(entry: DiagramEntry) -> str:
    if not entry.status:
        return "ohne_status"
    return entry.status if entry.status in DIAGRAM_STATUS else "unbekannt"


def _expired(entry: DiagramEntry, day: date) -> bool:
    try:
        return bool(entry.info and entry.info.valid_until and date.fromisoformat(entry.info.valid_until) < day)
    except ValueError:
        return False


def _coverage(entries: list[DiagramEntry]) -> dict[int, tuple[str, ...]]:
    coverage: dict[int, list[str]] = {}
    for entry in entries:
        for value in entry.excerpt.keys.get("ka", {}):
            if value.isdigit() and entry.id not in coverage.setdefault(int(value), []):
                coverage[int(value)].append(entry.id)
    return {number: tuple(ids) for number, ids in sorted(coverage.items())}


def overview(
    collection: DiagramCollection,
    folder_id: str | None = None,
    *,
    recursive: bool = True,
    tag_id: str | None = None,
    reference_date: date | None = None,
) -> GroupOverview:
    """Übersicht einer Gruppe (Ordner, rekursiv) oder eines Tags."""
    entries = (
        collection.with_tag(tag_id) if tag_id is not None else collection.diagrams_in(folder_id, recursive=recursive)
    )
    day = reference_date or date.today()
    return GroupOverview(
        count=len(entries),
        status_distribution=dict(sorted(Counter(_status(e) for e in entries).items())),
        activities=sum(e.excerpt.activities for e in entries),
        activities_with_legal_basis=sum(e.excerpt.activities_with_legal_basis for e in entries),
        expired=tuple(e.id for e in entries if _expired(e, day)),
        key_requirement_coverage=_coverage(entries),
        diagrams=tuple(e.id for e in entries),
    )


def _call_references(
    collection: DiagramCollection, entry: DiagramEntry, owners: dict[str, list[str]]
) -> list[DiagramReference]:
    result = []
    for element_id, called in entry.excerpt.calls:
        targets = owners.get(called, []) or ([called] if called in collection.diagrams else [])
        result.append(DiagramReference(entry.id, element_id, "aufruf", called, targets[0] if targets else None))
    return result


def _link_references(entry: DiagramEntry, catches: dict[str, list[tuple[str, str]]]) -> list[DiagramReference]:
    own = {name for _element, name in entry.excerpt.link_catches}
    result = []
    for element_id, name in entry.excerpt.link_throws:
        if name in own:
            continue
        target = next(((d, e) for d, e in catches.get(name, []) if d != entry.id), (None, None))
        result.append(DiagramReference(entry.id, element_id, "link", name, target[0], target[1]))
    return result


def process_owners(collection: DiagramCollection) -> dict[str, list[str]]:
    """Prozess-ID → Diagramme, die den Prozess enthalten."""
    owners: dict[str, list[str]] = {}
    for entry in collection.diagrams.values():
        for process_id in entry.excerpt.process_ids:
            owners.setdefault(process_id, []).append(entry.id)
    return owners


def references(collection: DiagramCollection) -> list[DiagramReference]:
    """Aufrufe (CallActivity → Prozess eines anderen Diagramms) und Link-Ereignisse über Diagrammgrenzen."""
    owners = process_owners(collection)
    catches: dict[str, list[tuple[str, str]]] = {}
    for entry in collection.diagrams.values():
        for element_id, name in entry.excerpt.link_catches:
            catches.setdefault(name, []).append((entry.id, element_id))
    result: list[DiagramReference] = []
    for entry in sorted(collection.diagrams.values(), key=lambda d: d.id):
        result += _call_references(collection, entry, owners)
        result += _link_references(entry, catches)
    return result


def target_actual_pairs(collection: DiagramCollection) -> list[tuple[str, str]]:
    """``(ist_id, soll_id)`` aller verknüpften Ist-Diagramme."""
    return sorted(
        (entry.id, entry.info.reference_diagram)
        for entry in collection.diagrams.values()
        if entry.info and entry.info.variant == "ist" and entry.info.reference_diagram
    )
