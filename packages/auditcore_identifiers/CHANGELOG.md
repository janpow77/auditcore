# Changelog – auditcore_identifiers

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
