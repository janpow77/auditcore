# Regulierung: native APT-Auslieferung

Regulierung bleibt im eigenen privaten Repository. Die Paketimplementierung liegt
auf `main` unter `deploy/apt/` (zuvor Branch `feat/native-apt-deployment`). Auditcore stellt die
Fachbibliotheken, SBOM-Erzeugung und den isolierten Paket-Lifecycle-Test bereit.
Anwendungsquellcode und Anwendungspakete werden nicht im öffentlichen Auditcore
veröffentlicht.

Zielplattform: Ubuntu 24.04 amd64 mit x86-64-v2-CPU, System-Python 3.12, PostgreSQL 16 mit
TimescaleDB/PostGIS und Redis. Ein Debian-12-/ARM64-Support wird nicht behauptet.
Backend und vorgebautes Frontend laufen als unprivilegierte systemd-Dienste,
lokal auf 8090 bzw. 3003. Der Zielserver benötigt keine Python-Paketdownloads,
Node-Buildwerkzeuge oder Compiler. Konfiguration und Daten bleiben außerhalb
von `/opt`; Installation führt weder Downloads noch automatische DB-Migrationen aus.

## Tatsächlich ausgeführte Prüfungen

Stand 26.09.2026: regulierung `5458d2e` (main nach PR #12 und #11) mit den
auditcore-Bibliotheken aus Release v0.4.1 (dataprotection 0.5.0, reporting 0.2.2,
harvest 0.1.2, price_analysis 0.1.2, price_sources 0.1.2, common 0.1.1, auth 0.1.0),
im Lock als Release-Wheels mit SHA-256; Frontend mit `@flowaudit/common`,
`@flowaudit/ui-core` und `@flowaudit/ui-react` als npm-pack-Tarballs aus auditcore.
Alembic-Head `owi049`.

- Anwendung: 1839 Tests bestanden, 1 übersprungen (benötigt `pg_dump` auf dem
  Testrechner; im Paket über `postgresql-client-16` vorhanden und im Lebenszyklus
  mit Sicherung/Wiederherstellung ausgeführt). Wegwerf-PostgreSQL 16.15 mit
  TimescaleDB 2.30.1/PostGIS 3.6.4; alle 88 gelockten Distributionen geprüft;
  Offline-Installation und `pip check` erfolgreich. Enthalten sind die
  Paritätstests alt ↔ Bibliothek (auditcore_auth, auditcore_common) und die
  Ausschlusstests für unlesbare Preiszeilen. Details: `application-tests.json`.
- Native Administrationslogik: 24 Tests bestanden; native Runtime/Readiness:
  19 Tests bestanden (letztere zusätzlich im Anwendungstestlauf enthalten).
- Vollständige Alembic-Neuinstallation bis `owi049` mit
  `NOSUPERUSER`-Anwendungsrolle erfolgreich ausgeführt; Extensions zuvor
  administrativ eingerichtet (PostgreSQL 16, TimescaleDB 2.30.1, PostGIS 3.6.4).
  `role-migration-proof.txt`.
- Paket-Lebenszyklus in QEMU (echtes systemd, offline, `-cpu max`): Installation,
  Upgrade (`-21` → `-22`), Entfernen und Neuinstallation mit signiertem lokalen
  APT-Feed; 31 Prüfpunkte PASS, darunter Anmeldung eines echten Administrators,
  Readiness (DB, Redis, Schema), Sicherung und Wiederherstellung vor dem Upgrade,
  Erhalt von Konfiguration und Daten, nativer PDF-Export. Gast mit TimescaleDB
  `2.30.1~ubuntu24.04-1615` und PostGIS `3.6.4+dfsg-2.pgdg24.04+1`; dieselben
  Versionen pinnt der Intranet-Installer (regulierung PR #13) und das
  Docker-Image `infra/postgres`. `lifecycle.json`.
- Frontend: Typprüfung, ESLint, Prettier, Vite-Build, Vitest in Europe/Berlin
  und America/New_York (113 Tests) und Chromium-Kartentest bestanden. Auth/API und
  Kartendaten waren im Browsertest Fixtures, keine Backend-Anmeldeprüfung.
  MapLibre 6.11.0 erfordert WebGL2/ES2022. Details: `frontend-tests.json`.
- Dependency-Audit: npm 2 moderate Befunde nur in der Testabhängigkeit vitest
  (nicht ausgeliefert); Python 81 öffentliche Pakete geprüft, ein verbleibendes
  ECDSA-Advisory betrifft ungenutzte Signier-/Keygen-Pfade. Die direkten Pins in
  `requirements.txt` (Docker-Pfad) sind deckungsgleich mit dem Lock.
  Anwendbarkeit und verbleibende Grenzen: `dependency-review.json` und
  `dependency-applicability.json`.
- CI-Build lokal in Ubuntu 24.04/CPython 3.12 tatsächlich ausgeführt
  (`ci_build.py`): öffentliche Wheels gegen feste Hashes, auditcore-Bibliotheken
  als Release-Wheels (kein Neubau aus dem Quellstand), Offline-Runtime und
  vollständiges `.deb`. `ci-rehearsal.json`. GitHub-Actions-Ausführung selbst:
  `NOT_EXECUTED`.

## Freigabegrenze

`policy-review.json` dokumentiert die erneute Framework-Auswertung gegen Commit
`15f5338f783f2c7d5760a9bb299be06d27326be0`. Schutzbedarf, konkrete KI-Nutzung,
Betriebsziel und betriebliche Nachweise bleiben teilweise `REVIEW_REQUIRED`.
Die Provider-Prüfung der Anwendbarkeit ersetzt keinen tatsächlich ausgeführten
Framework-Test. Ein Paketkandidat ist damit keine Produktionsfreigabe.

Die Tests verwenden ausschließlich synthetische Daten. Eine Übernahme vorhandener
Produktionsdaten, externe Identitätsprovider, Live-Harvesting, öffentliche
TLS-/Proxy-Konfiguration und schemaändernde Datenbank-Upgrades benötigen einen
konkreten Betriebs-/Migrationsnachweis. `regulierung-admin migrate` verweigert
unbewertete Schemaänderungen und prüft bei kompatiblen Updates zuvor Backup/Restore.
Der Zielserver des Ministeriums ist leer: ausgeliefert wird eine
Erstinstallation (`bootstrap-intranet`, alle Migrationen bis `owi049`); ein
Upgrade älterer Kandidaten (`owi047`/`owi048`) ist nicht Teil der Auslieferung.

## Reproduzierbarer Pakettest

Nach dem privaten Paketbuild können zwei tatsächlich gebaute Versionen geprüft werden:

Nach dem Paketdownload richtet ein Intranet-Administrator die Anwendung mit
einem einzigen interaktiven Schritt ein:

```bash
sudo apt install ./regulierung_....deb
sudo regulierung-admin bootstrap-intranet \
  --username admin --email admin@example.org
```

Der Befehl erkennt eine private Serveradresse und gibt die Login-URL aus. Eine
Adresse kann mit `--listen-address 192.168.1.50` fest vorgegeben werden.

Für den isolierten Upgrade-Nachweis:

```bash
printf '{}\n' > /tmp/regulierung-test.json
python scripts/regulierung_package_test.py /private/old.deb /private/new.deb \
  --configuration /tmp/regulierung-test.json --output .auditcore/regulierung-lifecycle
```

Der Test erstellt eine kurzlebige QEMU-VM mit echtem systemd und eigener Datenbank.
QEMU emuliert dafür eine CPU mit dem benötigten x86-64-v2-Befehlssatz
(`-cpu max`); das verwendete NumPy-Wheel meldet diese Baseline ausdrücklich.
Ein erster Lauf mit QEMUs älterer Standard-CPU scheiterte mit SIGILL und gilt
nicht als bestanden. Der VM fehlt eine Netzwerkkarte. Signierte APT-Feeds sind ausschließlich lokale
Testfeeds; der kurzlebige private Testschlüssel wird nicht veröffentlicht.
Der Host bekommt weder Anwendungspaket noch PostgreSQL-Installation.
