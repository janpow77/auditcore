"""Nominatim-Geocoder als Quellenadapter auf ``auditcore_harvest`` (Extra ``[geocoder]``).

Abgeleitet aus drei Anwendungen, die Nominatim bisher je selbst abfragen
(``osint`` ``werkzeuge/vorhaben_verorten.py:abfragen``, ``flowworkshop``
``services/geocoding_service.py:geocode_single``, ``audit_designer``
``api/vpai_notebook/gis/_common.py:_geocode_address``). Eine Seite des Laufs
ist genau **eine** Anfrage; Rate-Limit, Wiederholung, Zeitgrenzen, Senke und
Checkpoints übernimmt der ``HarvestEngine``. Der Adapter schläft nicht,
speichert nicht und bewertet keine Treffer (keine erfundene Konfidenz).

Nutzungsbedingungen des öffentlichen Dienstes (OSMF, abgerufen 23.09.2026,
https://operations.osmfoundation.org/policies/nominatim/): höchstens eine
Anfrage je Sekunde, ein einzelner Thread, identifizierender User-Agent
(keine Standardkennung von HTTP-Bibliotheken), Ergebnisse zwischenspeichern,
Namensnennung „© OpenStreetMap contributors“ (ODbL); Läufe über einen Tag
oder in regelmäßigen Abständen höchstens 4 Anfragen je Minute; keine
systematischen Abfragen (vollständige Listen von Postleitzahlen/Orten),
keine Autovervollständigung. Zusätzlich gilt nach Entscheidung vom
23.09.2026 eine Obergrenze von 1 000 Anfragen je Tag und Consumer.
:func:`pruefe_laufparameter` setzt die prüfbaren Punkte vor dem Lauf durch;
Zwischenspeicher und Tageszählung verantwortet der Consumer.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import urlsplit

from auditcore_harvest import (
    AuthKind,
    Capabilities,
    ConfigError,
    FetchContext,
    HarvestRecord,
    HarvestRequest,
    PageResult,
    PageStatus,
    ParserError,
    RateLimit,
    RecordIssue,
    SnapshotSemantics,
    Source,
    raise_for_status,
)

from . import __version__
from ._nominatim_daten import (
    _ANFRAGE_ID,
    _LAENDERCODES,
    _STANDARDKENNUNG,
    LAUFARTEN,
    MINDESTABSTAND_EINMALIG_S,
    MINDESTABSTAND_REGELMAESSIG_S,
    NAMENSNENNUNG,
    NUTZUNGSBEDINGUNGEN_URL,
    OEFFENTLICH_TAGESGRENZE,
    OEFFENTLICHER_ENDPUNKT,
    STRUKTUR_FELDER,
    Anfrage,
    _ein_treffer,
    _zahl,
    ist_oeffentlicher_endpunkt,
)

ADAPTER_VERSION = __version__
PROFILE_VERSION = "2026.09.1"

__all__ = [
    "ADAPTER_VERSION",
    "LAUFARTEN",
    "MINDESTABSTAND_EINMALIG_S",
    "MINDESTABSTAND_REGELMAESSIG_S",
    "NAMENSNENNUNG",
    "NUTZUNGSBEDINGUNGEN_URL",
    "OEFFENTLICHER_ENDPUNKT",
    "OEFFENTLICH_TAGESGRENZE",
    "PROFILE_VERSION",
    "STRUKTUR_FELDER",
    "Anfrage",
    "NominatimAdapter",
    "anfragen_aus",
    "empfohlene_laufparameter",
    "ist_oeffentlicher_endpunkt",
    "mindestabstand_s",
    "check_config",
    "pruefe_laufparameter",
]


def _strukturfelder(struktur: object, nummer: int) -> dict[str, str]:
    if not isinstance(struktur, Mapping) or not struktur:
        raise ConfigError(f"anfragen[{nummer}].strukturiert muss ein nichtleeres Objekt sein.")
    felder: dict[str, str] = {}
    for name, wert in struktur.items():
        if name not in STRUKTUR_FELDER:
            raise ConfigError(f"anfragen[{nummer}]: unbekanntes Feld {name!r}.")
        if not isinstance(wert, str) or not wert.strip():
            raise ConfigError(f"anfragen[{nummer}].{name} ist leer.")
        felder[name] = " ".join(wert.split())
    return felder


def _anfrage(roh: object, nummer: int) -> Anfrage:
    if not isinstance(roh, Mapping):
        raise ConfigError(f"anfragen[{nummer}] muss ein Objekt sein.")
    kennung = roh.get("id")
    if not isinstance(kennung, str) or not _ANFRAGE_ID.fullmatch(kennung):
        raise ConfigError(f"anfragen[{nummer}].id fehlt oder ist ungültig.")
    q = roh.get("q")
    struktur = roh.get("strukturiert")
    if (q is None) == (struktur is None):
        raise ConfigError(f"anfragen[{nummer}]: genau eines von q oder strukturiert angeben.")
    if q is not None:
        if not isinstance(q, str) or not q.strip():
            raise ConfigError(f"anfragen[{nummer}].q ist leer.")
        return Anfrage(kennung, q=" ".join(q.split()))
    return Anfrage(kennung, strukturiert=_strukturfelder(struktur, nummer))


def anfragen_aus(config: Mapping[str, object]) -> tuple[Anfrage, ...]:
    """Geprüfte Anfragen der Konfiguration; doppelte Kennungen sind ein Fehler."""
    roh = config.get("anfragen")
    if not isinstance(roh, Sequence) or isinstance(roh, (str, bytes)) or not roh:
        raise ConfigError("anfragen muss eine nichtleere Liste sein.")
    anfragen = tuple(_anfrage(a, i) for i, a in enumerate(roh))
    kennungen = [a.anfrage_id for a in anfragen]
    if len(set(kennungen)) != len(kennungen):
        raise ConfigError("Anfragekennungen sind nicht eindeutig.")
    return anfragen


def mindestabstand_s(basis_url: str, laufart: str) -> float:
    """Mindestabstand zweier Anfragen am Endpunkt; für eigene Instanzen 0 (Sache des Betreibers)."""
    if laufart not in LAUFARTEN:
        raise ConfigError(f"laufart muss einer von {LAUFARTEN} sein.")
    if not ist_oeffentlicher_endpunkt(basis_url):
        return 0.0
    return MINDESTABSTAND_REGELMAESSIG_S if laufart == "regelmaessig" else MINDESTABSTAND_EINMALIG_S


def _check_user_agent(kennung: object) -> None:
    if not isinstance(kennung, str) or len(kennung.strip()) < 3:
        raise ConfigError("user_agent muss die Anwendung identifizieren.")
    if _STANDARDKENNUNG.match(kennung):
        raise ConfigError("user_agent ist eine Standardkennung; Anwendung benennen.")


def _check_budget(budget: object, anzahl: int) -> int:
    if isinstance(budget, bool) or not isinstance(budget, int) or budget < 1:
        raise ConfigError("budget (Obergrenze der Anfragen) muss eine positive Zahl sein.")
    if anzahl > budget:
        raise ConfigError(f"{anzahl} Anfragen überschreiten das Budget {budget}.")
    return budget


def _check_base_url(basis: object, budget: int) -> str:
    if not isinstance(basis, str) or urlsplit(basis).scheme not in ("https", "http"):
        raise ConfigError("basis_url muss eine http(s)-Adresse sein.")
    if ist_oeffentlicher_endpunkt(basis) and urlsplit(basis).scheme != "https":
        raise ConfigError("Der öffentliche Endpunkt wird nur über https angesprochen.")
    if ist_oeffentlicher_endpunkt(basis) and budget > OEFFENTLICH_TAGESGRENZE:
        raise ConfigError(
            f"budget über der Tagesgrenze {OEFFENTLICH_TAGESGRENZE} des öffentlichen "
            "Endpunkts; eigene Nominatim-Instanz oder Import verwenden."
        )
    return basis


def _check_search_options(config: Mapping[str, object]) -> None:
    limit = config.get("limit", 1)
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 40:
        raise ConfigError("limit muss 1..40 sein.")
    laender = config.get("countrycodes")
    if laender is not None and (
        not isinstance(laender, str) or not _LAENDERCODES.fullmatch(laender)
    ):
        raise ConfigError("countrycodes: ISO-3166-1-alpha-2 klein, kommagetrennt.")
    for name in ("accept_language", "email"):
        wert = config.get(name)
        if wert is not None and (not isinstance(wert, str) or not wert.strip()):
            raise ConfigError(f"{name} ist leer.")
    if not isinstance(config.get("addressdetails", False), bool):
        raise ConfigError("addressdetails muss wahr/falsch sein.")


def check_config(config: Mapping[str, object]) -> None:
    """Konfiguration prüfen, ohne den Dienst anzufragen (Reihenfolge der Prüfungen fest)."""
    anfragen = anfragen_aus(config)
    _check_user_agent(config.get("user_agent"))
    budget = _check_budget(config.get("budget"), len(anfragen))
    basis = _check_base_url(config.get("basis_url", OEFFENTLICHER_ENDPUNKT), budget)
    mindestabstand_s(basis, str(config.get("laufart", "")))
    _check_search_options(config)


class NominatimAdapter:
    """``geo.nominatim_search``: eine Anfrage je Seite, ein Datensatz je Anfrage.

    Konfiguration (ohne Geheimnisse): ``anfragen`` (Liste ``{"id", "q"}``
    oder ``{"id", "strukturiert": {...}}``), ``user_agent`` (Pflicht,
    identifizierend), ``budget`` (Pflicht, Obergrenze der Anfragen),
    ``laufart`` (``einmalig``/``regelmaessig``), optional ``basis_url``,
    ``countrycodes``, ``limit`` (1–40, Vorgabe 1 wie in allen Quellen),
    ``accept_language``, ``email`` (Kontakt; wird nie aufgezeichnet),
    ``addressdetails``.
    """

    source = Source(
        source_id="geo.nominatim_search",
        title="Nominatim-Suche (OpenStreetMap)",
        family="geo",
        adapter_version=ADAPTER_VERSION,
        profile_version=PROFILE_VERSION,
        data_format="application/json",
        auth=AuthKind.NONE,
        capabilities=Capabilities(
            pagination=True, incremental=False, full_snapshot=False, deletions=False
        ),
        snapshot_semantics=SnapshotSemantics.UNKNOWN,
        filters=(),
    )

    def validate_config(self, config: Mapping[str, object]) -> None:
        """Konfiguration prüfen, ohne den Dienst anzufragen."""
        check_config(config)

    def _parameter(self, config: Mapping[str, object], anfrage: Anfrage) -> dict[str, str]:
        parameter = {
            **anfrage.parameter(),
            "format": "jsonv2",
            "limit": str(config.get("limit", 1)),
            "addressdetails": "1" if config.get("addressdetails", False) else "0",
        }
        if config.get("countrycodes"):
            parameter["countrycodes"] = str(config["countrycodes"])
        if config.get("accept_language"):
            parameter["accept-language"] = str(config["accept_language"])
        return parameter

    def fetch_page(self, context: FetchContext, cursor: Mapping[str, Any] | None) -> PageResult:
        """Genau eine Anfrage; der Datensatz enthält alle Treffer in Dienstreihenfolge."""
        anfragen = anfragen_aus(context.config)
        index = int(cursor["index"]) if cursor else 0
        if not 0 <= index < len(anfragen):
            raise ParserError(f"Cursor {index} außerhalb der {len(anfragen)} Anfragen.")
        anfrage = anfragen[index]
        basis = str(context.config.get("basis_url", OEFFENTLICHER_ENDPUNKT)).rstrip("/")
        parameter = self._parameter(context.config, anfrage)
        gesendet = dict(parameter)
        if context.config.get("email"):
            gesendet["email"] = str(context.config["email"])
        antwort = raise_for_status(
            context.transport.request(
                "GET",
                f"{basis}/search",
                params=gesendet,
                headers={"User-Agent": str(context.config["user_agent"])},
                timeout=context.timeout,
            )
        )
        try:
            daten = json.loads(antwort.body)
        except ValueError as exc:
            raise ParserError("Antwort des Geocoders ist kein JSON.") from exc
        if not isinstance(daten, list):
            raise ParserError("Antwort des Geocoders ist keine Trefferliste.")
        treffer, issues = _treffer(daten, anfrage.anfrage_id)
        lizenz = next(
            (str(t["licence"]) for t in daten if isinstance(t, Mapping) and t.get("licence")),
            NAMENSNENNUNG,
        )
        normalized: dict[str, object] = {
            "anfrage_id": anfrage.anfrage_id,
            "anfrage": parameter,
            "endpunkt": f"{basis}/search",
            "status": "treffer" if treffer else ("kein_treffer" if not daten else "ungueltig"),
            "anzahl": len(treffer),
            "treffer": treffer,
            "lizenz": lizenz,
        }
        record = HarvestRecord(
            source_id=self.source.source_id,
            record_id=anfrage.anfrage_id,
            raw=daten,
            normalized=normalized,
            provenance=context.provenance(self.source, f"anfrage/{anfrage.anfrage_id}", daten),
        )
        letzte = index + 1 >= len(anfragen)
        return PageResult(
            (record,),
            None if letzte else {"index": index + 1},
            letzte,
            PageStatus.PARTIAL if issues else PageStatus.OK,
            tuple(issues),
            len(anfragen),
        )


def _treffer(
    daten: Sequence[object], kennung: str
) -> tuple[list[dict[str, object]], list[RecordIssue]]:
    treffer: list[dict[str, object]] = []
    issues: list[RecordIssue] = []
    for rang, eintrag in enumerate(daten, 1):
        ort = f"anfrage/{kennung}/{rang}"
        if not isinstance(eintrag, Mapping):
            issues.append(RecordIssue(ort, "Treffer ist kein Objekt; nicht übernommen."))
            continue
        lat, lon = _zahl(eintrag.get("lat")), _zahl(eintrag.get("lon"))
        if lat is None or lon is None or not (-90 <= lat <= 90 and -180 <= lon <= 180):
            issues.append(RecordIssue(ort, "Treffer ohne gültige Koordinate; nicht übernommen."))
            continue
        treffer.append(_ein_treffer(rang, eintrag, lat, lon))
    return treffer, issues


def pruefe_laufparameter(
    config: Mapping[str, Any],
    rate_limit: RateLimit,
    request: HarvestRequest,
    *,
    heute_bereits_gesendet: int,
) -> None:
    """Vor dem Lauf: Mindestabstand, Budget und Tagesgrenze prüfen.

    Der Adapter kann den Takt nicht selbst durchsetzen (Adapter schlafen
    nicht); deshalb prüft der Consumer den Engine-Takt hier, bevor er
    ``engine.run`` aufruft. ``heute_bereits_gesendet`` zählt der Consumer
    (Anfragen dieses Consumers an denselben Endpunkt am laufenden Tag). Am
    öffentlichen Endpunkt dürfen damit höchstens
    :data:`OEFFENTLICH_TAGESGRENZE` Anfragen je Tag entstehen. Eine
    Verletzung ist ein :class:`ConfigError`.
    """
    NominatimAdapter().validate_config(config)
    if (
        isinstance(heute_bereits_gesendet, bool)
        or not isinstance(heute_bereits_gesendet, int)
        or heute_bereits_gesendet < 0
    ):
        raise ConfigError("heute_bereits_gesendet muss eine nicht negative ganze Zahl sein.")
    basis = str(config.get("basis_url", OEFFENTLICHER_ENDPUNKT))
    noetig = mindestabstand_s(basis, str(config["laufart"]))
    if rate_limit.min_interval_seconds < noetig:
        raise ConfigError(
            f"Rate-Limit {rate_limit.min_interval_seconds}s unterschreitet den Mindestabstand "
            f"{noetig}s des Endpunkts ({NUTZUNGSBEDINGUNGEN_URL})."
        )
    if request.max_pages > int(config["budget"]):
        raise ConfigError("max_pages des Laufs überschreitet das Budget.")
    if (
        ist_oeffentlicher_endpunkt(basis)
        and heute_bereits_gesendet + request.max_pages > OEFFENTLICH_TAGESGRENZE
    ):
        raise ConfigError(
            f"Tagesgrenze {OEFFENTLICH_TAGESGRENZE} Anfragen je Consumer am öffentlichen "
            f"Endpunkt überschritten ({heute_bereits_gesendet} bereits gesendet, "
            f"{request.max_pages} geplant); eigene Nominatim-Instanz oder Import verwenden."
        )


def empfohlene_laufparameter(
    config: Mapping[str, Any], run_id: str, *, heute_bereits_gesendet: int
) -> tuple[RateLimit, HarvestRequest]:
    """``RateLimit`` und ``HarvestRequest`` passend zu Endpunkt, Laufart, Budget und Tagesgrenze."""
    NominatimAdapter().validate_config(config)
    basis = str(config.get("basis_url", OEFFENTLICHER_ENDPUNKT))
    rate = RateLimit(mindestabstand_s(basis, str(config["laufart"])))
    anzahl = len(anfragen_aus(config))
    request = HarvestRequest(
        NominatimAdapter.source.source_id, run_id, max_pages=anzahl, max_records=anzahl
    )
    pruefe_laufparameter(config, rate, request, heute_bereits_gesendet=heute_bereits_gesendet)
    return rate, request
