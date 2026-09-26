# Changelog – auditcore_identifiers

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
