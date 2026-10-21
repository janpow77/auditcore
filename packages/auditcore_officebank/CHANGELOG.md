# Änderungen

## 0.1.0 – 2026-10-06

Erstmals veröffentlicht mit Release v0.9.0 (06.10.2026); in v0.14.0
unverändert enthalten.

- Etappe 0 (Gerüst): Rechnerprofil (`auditcore-officebank/rechner/1`) und
  Projektdatei `.officebank.toml` (`auditcore-officebank/projekt/1`) mit
  Schemaprüfung und JSON-Schemas als Paketdaten.
- Zentrale Ausgabe-Maskierung für Token, Passwörter und Verbindungszeichenfolgen.
- Gast-Schnittstelle `GuestBackend` mit `FakeGuest` für Tests ohne VM.
- CLI `auditcore-officebank` mit `status` und `konfig pruefen|schema`; die Gruppen
  der Etappen 1–6 sind angelegt und enden mit Exit 3.
- Typgerüste für Office, SQL-Server-Dienst, Build, Abnahme, Gates und Lieferung.
