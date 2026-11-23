# Changelog – auditcore_identifiers

## 0.3.0 – 2026-11-23

Korrekturen gegen falsch-positive Ergebnisse; neue Ergebnisfelder.

- **Neu:** `CheckResult.check_digit` (`CheckDigit`: `verified`, `failed`,
  `not_checked`, `none`) und die abgeleitete Eigenschaft `CheckResult.verdict`
  (`Verdict`: `valid` nur mit geprüfter Prüfziffer, sonst `format_valid`,
  `invalid`, `missing`). `to_dict()` enthält beide Felder; `status` bleibt
  unverändert (`VALID` = Format gültig). Legacy-Profile: `check_digit = None`,
  `verdict = format_valid`.
- **IBAN und LEI:** Prüfziffern `00`, `01` und `99` sind ungültig (ISO 7064
  MOD 97-10 erzeugt nur 02–98), auch wenn der Rest Modulo 97 eins ist.
- **USt-IdNr.:** nationale Prüfziffernverfahren aller 27 EU-Staaten
  (`vat_checks`, `vat_checks_mixed`, Tabelle `vat.CHECK_DIGIT_PROCEDURES`) und
  Strukturregeln in den Formaten (BE nicht nur Nullen, DK/MT/PT erste Ziffer
  ≠ 0, IT Amtscode, LT 8./11. Stelle `1`, NL nicht `B00`, CY nicht mit `12` beginnend, CZ 8-stellig nicht
  mit 9 beginnend, Geburtsdatum bei CZ/SK/BG/LV). Abgleich offline gegen
  python-stdnum 2.2 (Gültige und je eine verfälschte Nummer je Stichprobe); die
  Testnummern sind synthetisch (zufällig erzeugt, keiner Registerauskunft
  entnommen). `GB`/`XI` und französische Buchstabenschlüssel:
  `not_checked`, Meldung „Prüfziffer … nicht prüfbar“.
- **Handelsregisternummer:** Nummer ab 1 ohne führende Null (`HRB 0` ungültig);
  Registergericht vor oder hinter der Nummer wird abgetrennt
  (`details["court"]`); `check_digit = none`. Leerzeichenfolgen gelten als
  ein Zwischenraum, die Abtrennung läuft linear (kein Backtracking bei langen
  Leerzeichenfolgen aus OCR-Zeilen).
- **BIC:** `check_digit = none`, damit höchstens `format_valid`.
- **Steuer-ID** `verified`, **Steuernummer** `not_checked`.
- REST-Vertrag `identifiers_ui/1` erweitert (abwärtsverträglich): je Zeile
  `check_digit_label` und `verdict_label`, im Katalog `check_digit_labels` und
  `verdict_labels`, in der Stapelsumme `format_valid`.

## 0.2.1 – 2026-10-03

Gemeinsamer Release v0.6.0 mit aktuellem Paketstand, Dokumentation und
exakt gebundenen internen Abhängigkeiten.

## 0.2.0 – 2026-09-26 – Paketstand für Release v0.4.2

- Neue Laufzeitabhängigkeit `auditcore_common==0.2.0` (selbst nur
  Standardbibliothek): `web.ContractError` ist Unterklasse von
  `auditcore_common.rest.ContractError`, die JSON-Objekt-Prüfung nutzt
  `rest.json_object`. Meldungen, Statuscodes und Vertrag unverändert.
- REST-Vertrag `identifiers_ui/1` (`auditcore_identifiers.web`) für die
  Oberfläche „Kennung prüfen“: `GET /catalogue` (Kennungsarten, Profile mit
  ihren Arten, deutsche Bezeichnungen für Gründe und Einzelheiten, Grenzen),
  `POST /check` und `POST /check/batch` (Zeilenfehler für unbekannte oder
  vom Profil nicht geprüfte Arten statt Ablehnung der Tabelle). Neue Extras
  `web` (Starlette) und `fastapi`; der Kern bleibt ohne Abhängigkeiten.

## 0.1.0 – Erste Fassung

- Prüfen und Normalisieren von IBAN (ISO 13616: 89 Registerländer, BBAN-Aufbau,
  Modulo 97), BIC (ISO 9362:2014, ISO-3166-Land), USt-IdNr. (Formate aller
  EU-Staaten, XI, GB; Prüfziffer DE nach ISO 7064 MOD 11,10 und AT nach BMF),
  Steuer-ID (§ 139b AO: 11 Ziffern, Ziffernverteilung, Prüfziffer),
  Steuernummer (Landes- und 13-stelliges Bundesformat, grob), LEI (ISO 17442,
  Modulo 97) und Handelsregisternummer (Format).
- Einheitliches Ergebnisobjekt `CheckResult` mit Status, Grund, deutscher
  Meldung, Normalform und Details; keine Exceptions für ungültige Eingaben.
- Benannte Profile: `strict` (Standard) und sieben Legacy-Profile
  (`flowinvoice.legacy`, `audit_portal.legacy`, `flowinvoice.pipeline.legacy`,
  `audit_portal.pipeline.legacy`, `documents.donut`, `invoicesynth.legacy`,
  `flowworkshop.legacy`).
- Charakterisierung: 33 055 ausgeführte Originalaufrufe, Differenzbericht
  `docs/differences.md`, Gegenprüfung mit python-stdnum 2.2 (offline, als Daten).
