"""Legacy-compatible calculation of ``regulierung`` (exact replay, for consumer migration).

Reproduces ``backend/app/services/calculator.py`` and the pure selection
functions of ``backend/app/services/preisauswahl.py`` of
``janpow77/regulierung@853676d2`` byte-for-byte in results and error
messages; the characterization fixture replays every observed case. The
error texts are kept verbatim (including their ASCII transliterations)
because consumers and their tests match on them.

This module deliberately keeps the documented legacy findings (PA-L01 to
PA-L13 in ``docs/behavior-changes.md``), for example that a missing consumption
value or a missing optional component counts as zero. New code should use
:func:`auditcore_price_analysis.calculate` and the comparison functions, which
keep missing values visible.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any

# Umlagen-Stichtag: Ab 01.07.2025 gilt Wärmeumlagenpreis statt Gasspeicherumlage
UMLAGEN_STICHTAG = date(2025, 7, 1)
CENT = Decimal("0.01")
ZEHNTEL = Decimal("0.1")

# Toleranz beim Q3-Vergleich (Float-Spalte, Werte wie 2.5 / 4 / 6 / 10)
Q3_TOLERANZ = 0.01
DATENSTATUS_OK = "ok"
DATENSTATUS_KEIN_Q3_TARIF = "nicht_verfuegbar_fuer_q3"


def _decimal(value: object, *, feld: str, default: str = "0") -> Decimal:
    """Legacy: ``None`` wird zum Vorgabewert ``0`` (PA-L01)."""
    if value is None:
        value = default
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"{feld} muss eine gueltige Zahl sein") from exc
    if not result.is_finite():
        raise ValueError(f"{feld} muss endlich sein")
    return result


def _nicht_negativ(value: object, *, feld: str) -> Decimal:
    result = _decimal(value, feld=feld)
    if result < 0:
        raise ValueError(f"{feld} darf nicht negativ sein")
    return result


def _round(value: Decimal, places: Decimal = CENT) -> float:
    return float(value.quantize(places, rounding=ROUND_HALF_UP))


def calculate_nahwaerme(
    preisdaten: dict[str, Any],
    kw: Any = 12.0,
    kwh: Any = 27000.0,
    stichtag: str | date = "2025-01-01",
) -> dict[str, Any]:
    """Jahreskosten Nahwärme nach Anhang C (Legacy-Vertrag, exakt)."""
    if isinstance(stichtag, str):
        stichtag = date.fromisoformat(stichtag)

    kw_d = _nicht_negativ(kw, feld="kw")
    kwh_d = _nicht_negativ(kwh, feld="kwh")

    p_g = _nicht_negativ(preisdaten.get("grundpreis_eur_kw"), feld="grundpreis_eur_kw")
    p_a = _nicht_negativ(preisdaten.get("arbeitspreis_ct_kwh"), feld="arbeitspreis_ct_kwh")
    p_v = _nicht_negativ(
        preisdaten.get("verrechnungspreis_eur_jahr"), feld="verrechnungspreis_eur_jahr"
    )
    p_e = _nicht_negativ(preisdaten.get("emissionspreis_ct_kwh"), feld="emissionspreis_ct_kwh")

    if stichtag >= UMLAGEN_STICHTAG:
        umlage_typ = "waermeumlagenpreis"
        p_u = _nicht_negativ(
            preisdaten.get("waermeumlagenpreis_ct_kwh"), feld="waermeumlagenpreis_ct_kwh"
        )
    else:
        umlage_typ = "gasspeicherumlage"
        p_u = _nicht_negativ(preisdaten.get("umlagenpreis_ct_kwh"), feld="umlagenpreis_ct_kwh")

    grundpreis_anteil = p_g * kw_d
    arbeitspreis_anteil = p_a * kwh_d / 100
    verrechnungspreis_anteil = p_v
    emissionspreis_anteil = p_e * kwh_d / 100
    umlagenpreis_anteil = p_u * kwh_d / 100

    jahreskosten = (
        grundpreis_anteil
        + arbeitspreis_anteil
        + verrechnungspreis_anteil
        + emissionspreis_anteil
        + umlagenpreis_anteil
    )

    mischpreis_ct_kwh = (jahreskosten / kwh_d * 100) if kwh_d > 0 else Decimal(0)
    fixkosten = grundpreis_anteil + verrechnungspreis_anteil
    fixkostenanteil_pct = fixkosten / jahreskosten * 100 if jahreskosten > 0 else Decimal(0)
    variablekostenanteil_pct = Decimal(100) - fixkostenanteil_pct

    kern_komponenten = ("grundpreis_eur_kw", "arbeitspreis_ct_kwh")
    fehlende_komponenten = [k for k in kern_komponenten if preisdaten.get(k) is None]

    return {
        "jahreskosten": _round(jahreskosten),
        "vergleichsfaehig": not fehlende_komponenten,
        "fehlende_komponenten": fehlende_komponenten,
        "mischpreis_ct_kwh": _round(mischpreis_ct_kwh),
        "fixkostenanteil_pct": _round(fixkostenanteil_pct, ZEHNTEL),
        "variablekostenanteil_pct": _round(variablekostenanteil_pct, ZEHNTEL),
        "grundpreis_anteil": _round(grundpreis_anteil),
        "arbeitspreis_anteil": _round(arbeitspreis_anteil),
        "verrechnungspreis_anteil": _round(verrechnungspreis_anteil),
        "emissionspreis_anteil": _round(emissionspreis_anteil),
        "umlagenpreis_anteil": _round(umlagenpreis_anteil),
        "umlage_typ": umlage_typ,
        "parameter": {
            "kw": kw,
            "kwh": kwh,
            "stichtag": stichtag.isoformat(),
        },
    }


def calculate_wasser(
    preisdaten: dict[str, Any],
    q3: Any = 4.0,
    m3: Any = 150.0,
    stichtag: str | date = "2025-01-01",
) -> dict[str, Any]:
    """Jahreskosten Wasser (Legacy-Vertrag, exakt)."""
    if isinstance(stichtag, str):
        stichtag = date.fromisoformat(stichtag)

    _nicht_negativ(q3, feld="q3")
    m3_d = _nicht_negativ(m3, feld="m3")
    gp = _nicht_negativ(preisdaten.get("grundpreis_eur_monat"), feld="grundpreis_eur_monat")
    vp = _nicht_negativ(
        preisdaten.get("verrechnungspreis_eur_monat"), feld="verrechnungspreis_eur_monat"
    )
    wee = _nicht_negativ(
        preisdaten.get("wasserentnahmeentgelt_eur_m3"),
        feld="wasserentnahmeentgelt_eur_m3",
    )
    staffel = preisdaten.get("arbeitspreis_staffel")
    if isinstance(staffel, dict):
        staffel = staffel.get("staffeln", [])

    if isinstance(staffel, list) and len(staffel) > 0:
        arbeitspreis_anteil = _calculate_staffel_decimal(staffel, m3_d)
    else:
        ap = _nicht_negativ(preisdaten.get("arbeitspreis_eur_m3"), feld="arbeitspreis_eur_m3")
        arbeitspreis_anteil = m3_d * ap

    grundpreis_anteil = gp * 12
    verrechnungspreis_anteil = vp * 12
    wee_anteil = m3_d * wee

    jahreskosten = grundpreis_anteil + arbeitspreis_anteil + verrechnungspreis_anteil + wee_anteil
    mischpreis_eur_m3 = (jahreskosten / m3_d) if m3_d > 0 else Decimal(0)

    fehlende_komponenten: list[str] = []
    if preisdaten.get("grundpreis_eur_monat") is None:
        fehlende_komponenten.append("grundpreis_eur_monat")
    hat_staffel = isinstance(staffel, list) and len(staffel) > 0
    if not hat_staffel and preisdaten.get("arbeitspreis_eur_m3") is None:
        fehlende_komponenten.append("arbeitspreis_eur_m3")

    return {
        "jahreskosten": _round(jahreskosten),
        "vergleichsfaehig": not fehlende_komponenten,
        "fehlende_komponenten": fehlende_komponenten,
        "mischpreis_eur_m3": _round(mischpreis_eur_m3),
        "grundpreis_anteil": _round(grundpreis_anteil),
        "arbeitspreis_anteil": _round(arbeitspreis_anteil),
        "verrechnungspreis_anteil": _round(verrechnungspreis_anteil),
        "wee_anteil": _round(wee_anteil),
        "parameter": {
            "q3": q3,
            "m3": m3,
            "stichtag": stichtag.isoformat(),
        },
    }


def calculate_staffel(staffel: list[dict[str, Any]], m3: Any) -> float:
    """Arbeitspreis bei Staffeltarif (Legacy ``_calculate_staffel``)."""
    return _round(_calculate_staffel_decimal(staffel, _nicht_negativ(m3, feld="m3")))


_calculate_staffel = calculate_staffel


def _calculate_staffel_decimal(staffel: list[Any], m3: Decimal) -> Decimal:
    if not staffel:
        return Decimal(0)

    normalisiert: list[tuple[Decimal, Decimal]] = []
    for index, stufe in enumerate(staffel, start=1):
        if not isinstance(stufe, dict):
            raise ValueError(f"Staffelstufe {index} muss ein Objekt sein")
        limit = _nicht_negativ(stufe.get("bis_m3"), feld=f"Staffelstufe {index}.bis_m3")
        preis = _nicht_negativ(stufe.get("preis"), feld=f"Staffelstufe {index}.preis")
        if limit <= 0:
            raise ValueError(f"Staffelstufe {index}.bis_m3 muss groesser als 0 sein")
        normalisiert.append((limit, preis))

    normalisiert.sort(key=lambda item: item[0])
    if len({limit for limit, _ in normalisiert}) != len(normalisiert):
        raise ValueError("Staffelgrenzen muessen eindeutig sein")

    total = Decimal(0)
    remaining = m3
    prev_limit = Decimal(0)

    for i, (deklarierte_grenze, preis) in enumerate(normalisiert):
        ist_letzte = i == len(normalisiert) - 1
        band = remaining if ist_letzte else min(remaining, deklarierte_grenze - prev_limit)
        if band <= 0:
            continue
        total += band * preis
        remaining -= band
        prev_limit = deklarierte_grenze
        if remaining <= 0:
            break

    return total


def calculate_delta(aktuell: float, standard: float) -> float:
    """Prozentuale Abweichung (Legacy: Gleitkomma, ``round`` auf 1 Stelle; PA-L11)."""
    if standard == 0:
        return 0.0
    return round((aktuell - standard) / standard * 100, 1)


def determine_compliance(
    jahreskosten: float,
    cluster_median: float,
    schwelle_pct: float = 20.0,
) -> str:
    """Ampelstatus gruen/gelb/rot (Legacy: Gleitkomma, Median <= 0 ergibt gruen; PA-L12)."""
    if cluster_median <= 0:
        return "gruen"
    abweichung_pct = (jahreskosten - cluster_median) / cluster_median * 100
    if abweichung_pct <= schwelle_pct * 0.5:
        return "gruen"
    if abweichung_pct <= schwelle_pct:
        return "gelb"
    return "rot"


def calculate_cluster_statistics(jahreskosten_list: list[float]) -> dict[str, Any]:
    """Median, Mittel, Populations-Standardabweichung, Min, Max (Legacy; PA-L13)."""
    if not jahreskosten_list:
        return {"median": 0.0, "mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0, "count": 0}
    sorted_list = sorted(jahreskosten_list)
    n = len(sorted_list)
    if n % 2 == 0:
        median = (sorted_list[n // 2 - 1] + sorted_list[n // 2]) / 2
    else:
        median = sorted_list[n // 2]
    mean = sum(sorted_list) / n
    variance = sum((x - mean) ** 2 for x in sorted_list) / n
    stddev = variance**0.5
    return {
        "median": round(median, 2),
        "mean": round(mean, 2),
        "stddev": round(stddev, 2),
        "min": round(sorted_list[0], 2),
        "max": round(sorted_list[-1], 2),
        "count": n,
    }


def _sortier_schluessel(preis: Any) -> tuple[bool, Any, Any]:
    variant_id = getattr(preis, "variant_id", None)
    zeilen_id = getattr(preis, "id", None)
    return (
        variant_id is None,
        variant_id if variant_id is not None else 0,
        zeilen_id if zeilen_id is not None else 0,
    )


def waehle_preis_deterministisch(
    kandidaten: Sequence[Any],
    bevorzugte_variant_ids: set[int] | None = None,
) -> tuple[Any | None, bool]:
    """Neuester Stichtag gewinnt; bei Gleichstand stabil nach variant_id/id (Legacy)."""
    if not kandidaten:
        return None, False
    max_stichtag = max(p.stichtag for p in kandidaten)
    am_stichtag = [p for p in kandidaten if p.stichtag == max_stichtag]
    bevorzugt = [
        p
        for p in am_stichtag
        if getattr(p, "variant_id", None) in (bevorzugte_variant_ids or set())
    ]
    auswahl = bevorzugt or am_stichtag
    return sorted(auswahl, key=_sortier_schluessel)[0], len(am_stichtag) > 1


def waehle_wasser_preis(
    kandidaten: Sequence[Any],
    q3: float | None,
    bevorzugte_variant_ids: set[int] | None = None,
) -> tuple[Any | None, str, bool]:
    """Q3-Treffer bevorzugt, sonst Rückfall mit Datenstatus (Legacy)."""
    if not kandidaten:
        return None, DATENSTATUS_OK, False
    if q3 is not None:
        exakt = [
            p
            for p in kandidaten
            if p.zaehlergroesse_q3 is not None
            and abs(float(p.zaehlergroesse_q3) - float(q3)) < Q3_TOLERANZ
        ]
        if exakt:
            preis, mehrdeutig = waehle_preis_deterministisch(exakt, bevorzugte_variant_ids)
            return preis, DATENSTATUS_OK, mehrdeutig
        preis, mehrdeutig = waehle_preis_deterministisch(kandidaten, bevorzugte_variant_ids)
        return preis, DATENSTATUS_KEIN_Q3_TARIF, mehrdeutig
    preis, mehrdeutig = waehle_preis_deterministisch(kandidaten, bevorzugte_variant_ids)
    return preis, DATENSTATUS_OK, mehrdeutig
