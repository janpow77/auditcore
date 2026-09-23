# Regulierung: native APT-Auslieferung

Regulierung bleibt im eigenen privaten Repository. Die Paketimplementierung liegt
im Branch `feat/native-apt-deployment` unter `deploy/apt/`. Auditcore stellt die
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

- Anwendung: 1702 Tests bestanden, keine übersprungen. Disposable PostgreSQL mit
  TimescaleDB/PostGIS; alle 84 Runtime-Versionen gegen den Hashlock geprüft;
  Offline-Installation und `pip check` erfolgreich. Details: `application-tests.json`.
- Native Administrationslogik: 22 Tests bestanden; native Runtime/Readiness:
  19 Tests bestanden (letztere zusätzlich im Anwendungstestlauf enthalten).
- Vollständige Alembic-Neuinstallation bis `owi047` zusätzlich mit
  `NOSUPERUSER`-Anwendungsrolle erfolgreich ausgeführt; Extensions zuvor
  administrativ eingerichtet (PostgreSQL 16, TimescaleDB 2.30.0, PostGIS 3.6.4).
- Neue Bibliotheken: Datenschutz 413, Harvest 57 Tests bestanden; Ruff/Mypy bestanden.
- Auditcore-Plattform: 263 Tests; Ruff und Mypy bestanden.
- Frontend: TypeScript/Vite-Build und Chromium-Kartentest bestanden. Auth/API und
  Kartendaten waren im Browsertest Fixtures, keine Backend-Anmeldeprüfung.
  MapLibre 6.11.0 erfordert WebGL2/ES2022. Details: `frontend-tests.json`.
- Dependency-Audit: npm 0 Befunde; Python 81 öffentliche Pakete geprüft, ein
  verbleibendes ECDSA-Advisory betrifft ungenutzte Signier-/Keygen-Pfade.
  Anwendbarkeit und verbleibende Grenzen: `dependency-review.json` und
  `dependency-applicability.json`.
- Manueller CI-Build lokal in Ubuntu 24.04/CPython 3.12 tatsächlich ausgeführt:
  Wheels erstellt, Inhalte gegen getestete Wheels verglichen, Offline-Runtime
  installiert und vollständiges `.deb` gebaut. `ci-rehearsal.json`.
  GitHub-Actions-Ausführung selbst: `NOT_EXECUTED`.

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
