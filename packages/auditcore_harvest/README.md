# auditcore_harvest

Gemeinsamer, frameworkunabhängiger Kern für Datenharvester. Quellenpakete wie
`auditcore_funding_sources`, `auditcore_legal_sources` oder
`auditcore_procurement` implementieren Adapter; dieser Kern steuert Abruf,
Pagination, Zeitgrenzen, Rate-Limits, begrenzte Wiederholungen mit
`Retry-After`, Abbruch, Dubletten, idempotente Übergabe an eine Senke und
Checkpoints. Laufzeit: nur die Standardbibliothek; die Plattform `auditcore`
ist keine Abhängigkeit. Der Kern installiert keine Quellenadapter.

```bash
pip install auditcore_harvest==0.1.0
auditcore-harvest catalog        # versionierten Quellenkatalog prüfen
```

- Vertrag `auditcore_harvest.contract/1`: `Source`, `HarvestRequest`,
  `HarvestRecord`, `PageResult`, `Checkpoint`, `HarvestResult`, strukturierte
  Fehler (`auth`, `config`, `rate_limited`, `transport`, `parser`, `sink`, …).
- Ports: `Transport`, `CredentialProvider`, `StateStore`, `Sink`, `Clock`,
  `Sleeper`, `EventSink`. Mitgelieferte Transporte: `FileTransport`,
  `ReplayTransport`; Netzwerktransporte injiziert der Consumer
  (Beispiel ohne Zusatzpakete: `docs/examples/urllib_transport.py`).
- Zustellung *mindestens einmal*: Checkpoint erst nach Bestätigung der Senke;
  keine Exactly-once-Zusage. Der Kern löscht nie; `snapshot_complete` sagt,
  wann ein Consumer seine eigene Ersetzungsregel anwenden darf.
- `auditcore_harvest.testing`: wiederverwendbare Contract-Suite für Adapter.
- `auditcore_harvest.reference`: ausführbare Referenzadapter (JSON-API, RSS/Atom).

Anleitung für eigene Adapter: [docs/adapter-guide.md](docs/adapter-guide.md).
Bestandsbeobachtungen und Abweichungen: [docs/behavior-changes.md](docs/behavior-changes.md).

Scheduler, Datenbank, Mandanten, Anwendungsrechte und Zugangsdatenverwaltung
bleiben beim Consumer. Der Katalog nennt belegte Quellen mit Herkunft; ein
Eintrag bedeutet weder „implementiert“ noch „live getestet“.

Herkunft und Lizenz: siehe `NOTICE` und `provenance.json` (MIT, Freigabe des
Rechteinhabers vom 22.09.2026 für die Bibliothek; Quellrepositories und
Datenrechte der Dienste sind davon nicht erfasst). Debian-Paket:
`python3-auditcore-harvest`.
