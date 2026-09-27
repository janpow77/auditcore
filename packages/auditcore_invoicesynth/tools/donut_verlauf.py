#!/usr/bin/env python3
# ruff: noqa: E501 - SVG- und Tabellenzeilen bleiben lesbar am Stück
"""Verlaufsbericht Donut-Training: Kennzahlen je Stufe sammeln und als Markdown/SVG ausgeben.

    python tools/donut_verlauf.py            # sammeln (Host-Daten) + Bericht erzeugen
    python tools/donut_verlauf.py sammeln    # nur docs/donut-verlauf/kennzahlen.json aktualisieren
    python tools/donut_verlauf.py bericht    # nur Bericht aus kennzahlen.json (ohne Host-Daten)

Stufen stehen in ``docs/donut-verlauf/stufen.json``. Läufe eines GPU-Auftrags
(``~/.config/flow-agent/gpu-auftraege/<name>.json``) werden automatisch als weitere
Stufe ergänzt, sobald ihre Bewertung (``<donut>/eval/<lauf>.json``) vorliegt.
Nur Standardbibliothek; keine Vorhersagen, nur Kennzahlen landen im Repository.
"""

from __future__ import annotations

import json
import math
import sys
from datetime import UTC, datetime
from pathlib import Path

PAKET = Path(__file__).resolve().parents[1]
DOKU = PAKET / "docs"
ORDNER = DOKU / "donut-verlauf"
STUFEN = ORDNER / "stufen.json"
KENNZAHLEN = ORDNER / "kennzahlen.json"
BERICHT = DOKU / "donut-verlauf.md"

PFLICHT = {
    "total": 0.98,
    "invoice_date": 0.98,
    "invoice_number": 0.95,
    "iban": 0.97,
    "supplier.vat_id": 0.97,
}
MAX_FALSCH_NACH_PLAUSI = 0.005
FELDNAMEN = {
    "total": "Gesamtbetrag",
    "invoice_date": "Rechnungsdatum",
    "invoice_number": "Rechnungsnummer",
    "iban": "IBAN",
    "supplier.vat_id": "USt-IdNr.",
    "supplier.name": "Lieferant",
    "net_amount": "Nettobetrag",
    "vat_amount": "Steuerbetrag",
    "vat_rates": "Steuersätze",
    "due_date": "Fälligkeit",
    "supply_date": "Leistungsdatum",
    "bic": "BIC",
}
TESTSAETZE = {"test_synthetic": "T1 synthetisch", "test_layout_holdout": "T2 neue Layouts"}
KARTEN = {0: "RTX 5070 Ti", 1: "RTX 5060 Ti"}
# Okabe-Ito: auch bei Farbfehlsichtigkeit unterscheidbar
FARBEN = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9", "#D55E00"]
GRAU = "#8a8a8a"
PROFIL = {"image_size": "1280x960", "per_device_batch": 4, "grad_accum": 2, "seed": 42, "epochs": 6}


# --------------------------------------------------------------------------- sammeln


def _json(pfad: Path) -> dict:
    return json.loads(pfad.read_text(encoding="utf-8"))


def _option(befehl: list[str], name: str) -> str | None:
    return befehl[befehl.index(name) + 1] if name in befehl else None


def _konfiguration(root: Path, job: Path | None, lauf: str) -> dict:
    kfg: dict = {"karte": None, **PROFIL}
    if job is None or not job.exists():
        return kfg
    daten = _json(job)
    for spec in daten.get("runs", daten.get("laeufe", [])):
        befehl = [str(a) for a in spec.get("command", [])]
        run_dir = _option(befehl, "--run-dir") or spec.get("run_dir", "")
        if Path(run_dir).name != lauf:
            continue
        gpus = spec.get("gpus") or []
        karte = spec.get("gpu", spec.get("gpu_index", gpus[0] if gpus else None))
        kfg["karte"] = int(karte) if karte is not None else None
        for schluessel, option, art in (
            ("image_size", "--image-size", str),
            ("per_device_batch", "--per-device-batch", int),
            ("grad_accum", "--grad-accum", int),
            ("seed", "--seed", int),
            ("epochs", "--epochs", int),
        ):
            wert = _option(befehl, option)
            if wert is not None:
                kfg[schluessel] = art(wert)
        datensatz = _option(befehl, "--dataset") or ""
        kfg["datensatz_hash"] = Path(datensatz).name[:16]
        kfg["max_stunden"] = spec.get("max_stunden") or daten.get("dauer_stunden")
    return kfg


def _training(run_dir: Path, punkte: int = 240) -> dict:
    log = run_dir / "train-log.jsonl"
    if not log.exists():
        return {}
    zeilen = [json.loads(z) for z in log.read_text(encoding="utf-8").splitlines() if z.strip()]
    zeilen = [
        z for z in zeilen if isinstance(z.get("loss"), int | float) and math.isfinite(z["loss"])
    ]
    if not zeilen:
        return {}
    fortschritt = {}
    if (run_dir / "progress.json").exists():
        fortschritt = _json(run_dir / "progress.json")
    gesamt = int(fortschritt.get("schritte_gesamt") or zeilen[-1]["step"])
    eimer = max(1, math.ceil(len(zeilen) / punkte))
    kurve = []
    for i in range(0, len(zeilen), eimer):
        teil = zeilen[i : i + eimer]
        kurve.append([teil[-1]["step"], round(sum(z["loss"] for z in teil) / len(teil), 5)])
    dauer = zeilen[-1]["time"] - zeilen[0]["time"] if "time" in zeilen[0] else None
    return {
        "schritte": zeilen[-1]["step"],
        "schritte_gesamt": gesamt,
        "zustand": fortschritt.get("zustand"),
        "dauer_h": round(dauer / 3600, 2) if dauer else None,
        "loss_start": round(sum(z["loss"] for z in zeilen[:20]) / min(20, len(zeilen)), 4),
        "loss_ende": round(sum(z["loss"] for z in zeilen[-50:]) / min(50, len(zeilen)), 5),
        "vram_spitze_gib": max((z.get("vram_peak_gib") or 0) for z in zeilen),
        "kurve": kurve,
    }


def _bewertung(pfad: Path) -> dict:
    roh = _json(pfad)["results"]
    aus: dict = {}
    for modell, saetze in roh.items():
        aus[modell] = {}
        for satz, werte in saetze.items():
            felder = {}
            for feld, f in werte["fields"].items():
                felder[feld] = {
                    k: f.get(k)
                    for k in (
                        "accuracy",
                        "correct",
                        "expected",
                        "missing",
                        "wrong",
                        "hallucinated",
                        "accepted",
                        "accepted_wrong",
                    )
                }
            aus[modell][satz] = {
                "belege": werte["documents"],
                "belegquote": werte["document_rate"],
                "sek_pro_seite": werte["seconds_per_page"]["median"],
                "abnahme": werte["acceptance"]["passed"],
                "abnahme_fehler": werte["acceptance"]["failures"],
                "felder": felder,
            }
    return aus


def sammeln() -> dict:
    cfg = _json(STUFEN)
    root = Path(cfg["donut_root"])
    stufen = list(cfg["stufen"])
    auftraege = Path(cfg.get("auftraege_ordner", "~/.config/flow-agent/gpu-auftraege")).expanduser()
    for name in cfg.get("gpu_auftraege", []):
        job = auftraege / f"{name}.json"
        if not job.exists():
            continue
        daten = _json(job)
        for nr, spec in enumerate(daten.get("runs", daten.get("laeufe", []))):
            run_dir = _option([str(a) for a in spec.get("command", [])], "--run-dir")
            if not run_dir:
                continue
            lauf = Path(run_dir).name
            if any(s["run"] == lauf for s in stufen):
                continue
            stufen.append(
                {
                    "id": f"{name}-{nr}",
                    "titel": f"{cfg.get('titel_auftraege', {}).get(name, name)}, Lauf {nr + 1}",
                    "run": lauf,
                    "eval": f"eval/{lauf}.json",
                    "job": str(job),
                    "testsaetze": "voll",
                }
            )
    ergebnis = {"erzeugt": datetime.now(UTC).isoformat(timespec="seconds"), "stufen": []}
    for stufe in stufen:
        job = stufe.get("job")
        job_pfad = Path(job) if job and Path(job).is_absolute() else (root / job if job else None)
        eintrag = {
            **{k: stufe[k] for k in ("id", "titel", "run", "testsaetze")},
            "hinweis": stufe.get("hinweis"),
            "konfiguration": _konfiguration(root, job_pfad, stufe["run"]),
            "training": _training(root / "runs" / stufe["run"]),
        }
        eval_pfad = root / stufe["eval"]
        eintrag["bewertung"] = _bewertung(eval_pfad) if eval_pfad.exists() else None
        ergebnis["stufen"].append(eintrag)
    KENNZAHLEN.write_text(
        json.dumps(ergebnis, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    return ergebnis


# --------------------------------------------------------------------------- Diagramme


def _svg_kopf(breite: int, hoehe: int, titel: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{breite}" height="{hoehe}" '
        f'viewBox="0 0 {breite} {hoehe}" font-family="DejaVu Sans, Arial, sans-serif" font-size="12">',
        f"<title>{titel}</title>",
        f'<rect width="{breite}" height="{hoehe}" fill="#ffffff"/>',
        f'<text x="16" y="22" font-size="14" font-weight="bold" fill="#1f2937">{titel}</text>',
    ]


def svg_loss(stufen: list[dict]) -> str:
    b, h, li, r, o, u = 760, 360, 64, 190, 40, 44
    zeichnen = [s for s in stufen if s["training"].get("kurve")]
    alle = [p[1] for s in zeichnen for p in s["training"]["kurve"] if p[1] > 0]
    lo, hi = math.log10(max(min(alle), 1e-5)), math.log10(max(alle))
    lo, hi = math.floor(lo), math.ceil(hi)
    teile = _svg_kopf(b, h, "Trainings-Loss je Stufe (gleitender Mittelwert, log. Achse)")
    x = lambda f: li + f * (b - li - r)  # noqa: E731
    y = lambda v: o + (hi - math.log10(max(v, 1e-5))) / (hi - lo) * (h - o - u)  # noqa: E731
    for e in range(lo, hi + 1):
        teile.append(
            f'<line x1="{li}" x2="{b - r}" y1="{y(10**e):.1f}" y2="{y(10**e):.1f}" stroke="#e5e7eb"/>'
        )
        teile.append(
            f'<text x="{li - 8}" y="{y(10**e) + 4:.1f}" text-anchor="end" fill="#4b5563">1e{e}</text>'
        )
    for f in (0, 0.25, 0.5, 0.75, 1):
        teile.append(
            f'<text x="{x(f):.1f}" y="{h - u + 18}" text-anchor="middle" fill="#4b5563">{int(f * 100)} %</text>'
        )
    teile.append(
        f'<text x="{(li + b - r) / 2}" y="{h - 8}" text-anchor="middle" fill="#4b5563">Anteil des Trainings (Schritt / Schritte gesamt)</text>'
    )
    for i, s in enumerate(zeichnen):
        farbe = FARBEN[i % len(FARBEN)]
        gesamt = s["training"]["schritte_gesamt"] or s["training"]["schritte"]
        punkte = " ".join(f"{x(p[0] / gesamt):.1f},{y(p[1]):.1f}" for p in s["training"]["kurve"])
        teile.append(f'<polyline fill="none" stroke="{farbe}" stroke-width="2" points="{punkte}"/>')
        ly = o + 18 + i * 20
        teile.append(
            f'<line x1="{b - r + 14}" x2="{b - r + 34}" y1="{ly - 4}" y2="{ly - 4}" stroke="{farbe}" stroke-width="3"/>'
        )
        teile.append(f'<text x="{b - r + 40}" y="{ly}" fill="#1f2937">{s["titel"]}</text>')
    teile.append("</svg>")
    return "\n".join(teile) + "\n"


def svg_felder(reihen: list[tuple[str, dict, str]], satz: str) -> str:
    felder = list(PFLICHT) + [f for f in FELDNAMEN if f not in PFLICHT]
    b, li, r, o = 820, 130, 24, 64
    zeile = 14 * len(reihen) + 10
    h = o + zeile * len(felder) + 40
    teile = _svg_kopf(
        b, h, f"Feldgenauigkeit {TESTSAETZE[satz]} je Stufe (Strich = Abnahmeschwelle)"
    )
    x = lambda v: li + v * (b - li - r)  # noqa: E731
    for f in (0, 0.25, 0.5, 0.75, 1):
        teile.append(
            f'<line x1="{x(f):.1f}" x2="{x(f):.1f}" y1="{o - 6}" y2="{h - 34}" stroke="#e5e7eb"/>'
        )
        teile.append(
            f'<text x="{x(f):.1f}" y="{h - 18}" text-anchor="middle" fill="#4b5563">{int(f * 100)} %</text>'
        )
    for j, (titel, _, farbe) in enumerate(reihen):
        teile.append(
            f'<rect x="{li + j * 170}" y="{o - 30}" width="12" height="12" fill="{farbe}"/>'
        )
        teile.append(f'<text x="{li + j * 170 + 18}" y="{o - 20}" fill="#1f2937">{titel}</text>')
    for i, feld in enumerate(felder):
        y0 = o + i * zeile
        teile.append(
            f'<text x="{li - 8}" y="{y0 + zeile / 2 + 2:.1f}" text-anchor="end" fill="#1f2937">{FELDNAMEN[feld]}</text>'
        )
        for j, (_, werte, farbe) in enumerate(reihen):
            wert = (werte.get(feld) or {}).get("accuracy") or 0
            teile.append(
                f'<rect x="{li}" y="{y0 + j * 14}" width="{x(wert) - li:.1f}" height="12" fill="{farbe}"/>'
            )
        if feld in PFLICHT:
            sx = x(PFLICHT[feld])
            teile.append(
                f'<line x1="{sx:.1f}" x2="{sx:.1f}" y1="{y0 - 2}" y2="{y0 + zeile - 8}" stroke="#111827" stroke-width="2"/>'
            )
    teile.append("</svg>")
    return "\n".join(teile) + "\n"


# --------------------------------------------------------------------------- Bericht


def _p(wert: float | None, stellen: int = 1) -> str:
    return "–" if wert is None else f"{wert * 100:.{stellen}f}".replace(".", ",")


def _z(wert: float | None, stellen: int = 2) -> str:
    return "–" if wert is None else f"{wert:.{stellen}f}".replace(".", ",")


def _ganz(wert: int | None) -> str:
    return "–" if wert is None else f"{wert:,}".replace(",", " ")


def _plausi_gemessen(stufen: list[dict]) -> bool:
    return any(
        (f.get("accepted") or 0) > 0
        for s in stufen
        if s["bewertung"]
        for satz in s["bewertung"]["kandidat"].values()
        for f in satz["felder"].values()
    )


def bericht(daten: dict) -> str:
    stufen = daten["stufen"]
    bewertet = [s for s in stufen if s["bewertung"]]
    voll = [s for s in bewertet if s["testsaetze"] == "voll"]
    pilot = [s for s in bewertet if s["testsaetze"] == "pilot"]
    offen = [s for s in stufen if not s["bewertung"]]
    zeilen = [
        "# Donut-Training: Verlauf der Ergebnisse",
        "",
        f"Stand {daten['erzeugt'][:10]} · erzeugt mit `tools/donut_verlauf.py` aus den Läufen auf janpow-ai "
        "(Kennzahlen: `docs/donut-verlauf/kennzahlen.json`). Hintergrund, Datensätze und Aufrufe: "
        "[training.md](training.md).",
        "",
        "## Vergleichbarkeit",
        "",
        "- **Stufe 0** ist das unveränderte Donut-CORD-Modell (`naver-clova-ix/donut-cord-v2`); es kennt das "
        "Rechnungsschema nicht und dient nur als Nullpunkt.",
        "- **Pilot** und **Volllauf** wurden auf **unterschiedlichen Testsätzen** bewertet: der Pilot auf den "
        "Testsätzen des Pilot-Datensatzes (T1 163 / T2 100 Belege), alle späteren Stufen auf denen des "
        "Vollsatzes (T1 1 121 / T2 500 Belege). Beide stammen aus demselben Generator, sind aber verschiedene "
        "Belege; Unterschiede von wenigen Prozentpunkten zwischen Pilot und Volllauf sind deshalb nicht belastbar.",
        "- T1 = synthetische Belege aus den Trainingsvorlagen, T2 = Layouts und Schriften, die im Training nie "
        "vorkamen. Für die Praxis zählt T2.",
        "- Abnahme (Entscheidung E6): Pflichtfelder mit Mindestgenauigkeit, zusätzlich höchstens "
        f"{_p(MAX_FALSCH_NACH_PLAUSI)} % Falschwerte nach Plausibilitätsprüfung je Feld. "
        + (
            "Die Bewertung (`train/evaluate.py`) läuft derzeit **ohne** Plausibilitätsprüfung; das zweite "
            "Kriterium ist deshalb nicht gemessen, geprüft wird nur die Feldgenauigkeit."
            if not _plausi_gemessen(stufen)
            else ""
        ),
        "",
        "## Stufen",
        "",
        "| Stufe | Lauf | Karte | Datensatz | Bildgröße | Batch × Akk. | Seed | Epochen | Schritte | Dauer | Loss Start → Ende |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
        "| 0 · Donut-CORD | – | – | – | – | – | – | – | – | – | – |",
    ]
    for s in stufen:
        k, t = s["konfiguration"], s["training"]
        karte = KARTEN.get(k.get("karte"), "–") if k.get("karte") is not None else "–"
        schritte = f"{_ganz(t.get('schritte'))} / {_ganz(t.get('schritte_gesamt'))}" if t else "–"
        zeilen.append(
            f"| {s['titel']} | `{s['run']}` | {karte} | {'Pilot' if s['testsaetze'] == 'pilot' else 'Voll'} | "
            f"{k['image_size'].replace('x', '×')} | {k['per_device_batch']} × {k['grad_accum']} | {k['seed']} | "
            f"{k['epochs']} | {schritte} | {_z(t.get('dauer_h'), 1) + ' h' if t.get('dauer_h') else '–'} | "
            f"{_z(t.get('loss_start'))} → {_z(t.get('loss_ende'), 4) if t else '–'} |"
        )
    zeilen += ["", "![Loss-Verlauf](donut-verlauf/loss.svg)", ""]

    def kernzahlen(gruppe: list[dict], ueberschrift: str) -> None:
        if not gruppe:
            return
        zeilen.extend(
            [
                f"## {ueberschrift}",
                "",
                "| Stufe | Belegquote T1 | Belegquote T2 | s/Seite (T2) | Abnahme T1 | Abnahme T2 |",
                "|---|---|---|---|---|---|",
            ]
        )
        cord = gruppe[0]["bewertung"].get("donut_cord", {})
        if cord:
            zeilen.append(
                f"| 0 · Donut-CORD | {_p(cord['test_synthetic']['belegquote'])} % | "
                f"{_p(cord['test_layout_holdout']['belegquote'])} % | "
                f"{_z(cord['test_layout_holdout']['sek_pro_seite'])} | nein | nein |"
            )
        for s in gruppe:
            k = s["bewertung"]["kandidat"]
            zeilen.append(
                f"| {s['titel']} | {_p(k['test_synthetic']['belegquote'])} % | "
                f"{_p(k['test_layout_holdout']['belegquote'])} % | {_z(k['test_layout_holdout']['sek_pro_seite'])} | "
                f"{'ja' if k['test_synthetic']['abnahme'] else 'nein'} | "
                f"{'ja' if k['test_layout_holdout']['abnahme'] else 'nein'} |"
            )
        zeilen.append("")
        zeilen.append(
            "Belegquote = Anteil der Belege, bei denen **alle fünf Pflichtfelder** stimmen "
            "(Gesamtbetrag, Rechnungsdatum, Rechnungsnummer, IBAN, USt-IdNr.)."
        )
        zeilen.append("")

    kernzahlen(
        pilot,
        f"Kernzahlen auf den Pilot-Testsätzen (T1 {pilot[0]['bewertung']['kandidat']['test_synthetic']['belege'] if pilot else '–'} / T2 {pilot[0]['bewertung']['kandidat']['test_layout_holdout']['belege'] if pilot else '–'} Belege)",
    )
    kernzahlen(
        voll,
        f"Kernzahlen auf den Voll-Testsätzen (T1 {voll[0]['bewertung']['kandidat']['test_synthetic']['belege'] if voll else '–'} / T2 {voll[0]['bewertung']['kandidat']['test_layout_holdout']['belege'] if voll else '–'} Belege)",
    )

    for satz in ("test_layout_holdout", "test_synthetic"):
        zeilen += [
            f"## Feldgenauigkeit {TESTSAETZE[satz]}",
            "",
            "| Feld | Schwelle | "
            + " | ".join(s["titel"] + ("¹" if s["testsaetze"] == "pilot" else "") for s in bewertet)
            + " |",
            "|---|---|" + "---|" * len(bewertet),
        ]
        for feld, name in FELDNAMEN.items():
            werte = []
            for s in bewertet:
                acc = s["bewertung"]["kandidat"][satz]["felder"].get(feld, {}).get("accuracy")
                ok = feld in PFLICHT and acc is not None and acc >= PFLICHT[feld]
                werte.append(f"{'**' if ok else ''}{_p(acc)} %{'**' if ok else ''}")
            schwelle = f"{_p(PFLICHT[feld], 0)} %" if feld in PFLICHT else "–"
            zeilen.append(
                f"| {name}{' (Pflicht)' if feld in PFLICHT else ''} | {schwelle} | "
                + " | ".join(werte)
                + " |"
            )
        zeilen += [
            "",
            "Fett = Abnahmeschwelle erreicht. ¹ Pilot-Testsatz (andere, kleinere Stichprobe).",
            "",
        ]
        if satz == "test_layout_holdout" and bewertet:
            zeilen += [f"![Feldgenauigkeit {TESTSAETZE[satz]}](donut-verlauf/felder-t2.svg)", ""]

    letzte = bewertet[-1] if bewertet else None
    if letzte:
        zeilen += [
            f"## Fehlerbild der Pflichtfelder auf T2 ({letzte['titel']})",
            "",
            "| Feld | erwartet | richtig | fehlt | falsch | davon erfunden |",
            "|---|---|---|---|---|---|",
        ]
        for feld in PFLICHT:
            f = letzte["bewertung"]["kandidat"]["test_layout_holdout"]["felder"].get(feld, {})
            e = f.get("expected") or 0
            q = lambda n, e=e: f"{_ganz(n)} ({_p((n or 0) / e if e else None, 0)} %)"  # noqa: E731
            zeilen.append(
                f"| {FELDNAMEN[feld]} | {_ganz(e)} | {q(f.get('correct'))} | {q(f.get('missing'))} | "
                f"{q(f.get('wrong'))} | {q(f.get('hallucinated'))} |"
            )
        zeilen += [
            "",
            "Fehlt = kein Wert ausgegeben. Falsch = Wert ausgegeben, aber nicht der erwartete. "
            "Erfunden = ausgegebener Wert, der in keinem erwarteten Feld dieses Belegs vorkommt. Ein fehlender Wert ist "
            "für die Prüfung harmloser als ein falscher, weil er auffällt.",
            "",
        ]

    zeilen += ["## Stufe 3: Läufe mit großen Bildern (1536×1152)", ""]
    grosse = [
        s for s in stufen if s["konfiguration"]["image_size"] == "1536x1152" and s["training"]
    ]
    if not grosse:
        zeilen.append(
            "_Noch offen._ Die Läufe mit großen Bildern (GPU-Auftrag `donut-gross`, beide Karten, "
            "höchstens 8 h) werden nach ihrem Ende bewertet; danach wird dieser Bericht mit "
            "`tools/donut_verlauf.py` neu erzeugt."
        )
    else:
        for s in grosse:
            zustand = "bewertet" if s["bewertung"] else "noch nicht bewertet"
            zeilen.append(
                f"- {s['titel']} (`{s['run']}`): {zustand}, Training {s['training'].get('zustand')}, "
                f"{_ganz(s['training'].get('schritte'))} von {_ganz(s['training'].get('schritte_gesamt'))} Schritten."
            )
    if offen:
        zeilen += ["", "Ohne Bewertung: " + ", ".join(f"`{s['run']}`" for s in offen) + "."]
    return "\n".join(zeilen) + "\n"


def bericht_schreiben(daten: dict) -> None:
    ORDNER.mkdir(parents=True, exist_ok=True)
    (ORDNER / "loss.svg").write_text(svg_loss(daten["stufen"]), encoding="utf-8")
    bewertet = [s for s in daten["stufen"] if s["bewertung"]]
    reihen = []
    if bewertet:
        cord_quelle = next((s for s in bewertet if s["testsaetze"] == "voll"), bewertet[0])
        reihen.append(
            (
                "0 · Donut-CORD",
                cord_quelle["bewertung"]["donut_cord"]["test_layout_holdout"]["felder"],
                GRAU,
            )
        )
    for i, s in enumerate(bewertet):
        reihen.append(
            (
                s["titel"],
                s["bewertung"]["kandidat"]["test_layout_holdout"]["felder"],
                FARBEN[i % len(FARBEN)],
            )
        )
    if reihen:
        (ORDNER / "felder-t2.svg").write_text(
            svg_felder(reihen, "test_layout_holdout"), encoding="utf-8"
        )
    BERICHT.write_text(bericht(daten), encoding="utf-8")


def main(argv: list[str]) -> int:
    modus = argv[1] if len(argv) > 1 else "alles"
    if modus not in {"alles", "sammeln", "bericht"}:
        print(__doc__)
        return 2
    daten = sammeln() if modus in {"alles", "sammeln"} else _json(KENNZAHLEN)
    if modus in {"alles", "bericht"}:
        bericht_schreiben(daten)
    print(f"{len(daten['stufen'])} Stufen, Bericht: {BERICHT}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
