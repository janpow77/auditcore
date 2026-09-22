# Echte systemd-Dienstprüfung in einer isolierten VM

Der vorhandene `DockerPackageTester` prüft Paketinstallation, Upgrade,
Entfernung und einen direkt gestarteten HTTP-Prozess. Ein gewöhnlicher
Docker-Container konnte systemd wegen des schreibgeschützten cgroup-Mounts
nicht als PID 1 starten. `systemd-analyze verify` ersetzt den Dienstlauf nicht.

`scripts/systemd_package_test.py` verwendet deshalb einen eigenen Debian-Kernel
in einer QEMU-VM. QEMU läuft mit CPU-Emulation als unprivilegierter Benutzer in
einem gewöhnlichen Docker-Container. Weder KVM noch ein privilegierter Container,
Host-cgroup-Mounts, Hostpaketinstallationen oder Änderungen an Hostdiensten sind
erforderlich. Der Container hat keine Capabilities, ein schreibgeschütztes
Root-Dateisystem und ein begrenztes temporäres Dateisystem für den VM-Snapshot.
Die VM hat keine Netzwerkkarte; auch das Container-Netzwerk ist abgeschaltet.

Nur der Aufbau des Testimages lädt Debian-Pakete. Bei der Paketinstallation im
Gast verhindern `--no-download` und die fehlende Netzwerkkarte Downloads.
Anwendungsspezifische Debian-Abhängigkeiten müssen bereits im Testimage vorhanden
sein; fehlende Abhängigkeiten führen zu einem Fehler.

## Ausführung

Voraussetzungen: Docker auf Linux/amd64, Python 3.11 oder neuer und zwei Paketversionen
derselben Anwendung. Der folgende Aufruf prüft die bestehenden **synthetischen
Testpakete**, keine reale Fachanwendung:

```bash
python3 scripts/systemd_package_test.py \
  .auditcore/package-lifecycle/auditcore-fixture_1.0.0_all.deb \
  .auditcore/package-lifecycle/auditcore-fixture_1.1.0_all.deb \
  --output .auditcore/systemd-validation-lifecycle
```

`result.json` enthält Artefakthashes, Testimage-Digest, Gastkernel,
systemd-Version, PID-1-Nachweis und getrennte Prüfergebnisse. `build.log` und
`console.log` enthalten die tatsächlichen Befehlsausgaben. Das Testimage bleibt
für die Nachvollziehbarkeit lokal erhalten; der eigens benannte Testcontainer
wird entfernt. Bestehende Container werden nicht angesprochen.

Die Prüfung installiert Version 1, aktiviert und startet deren Dienst, prüft
die von systemd verwaltete MainPID und die tatsächliche Prozess-UID, führt den
Healthcheck aus und wiederholt dies nach Upgrade auf Version 2. Anschließend
wird das Paket entfernt. Konfiguration und persistente Testdaten müssen nach
Upgrade und Entfernung erhalten bleiben; nach Entfernung muss der Dienst
beendet sein. Bei den vorhandenen Fixtures ist automatischer Start durch
`postinst` absichtlich nicht konfiguriert. Der Test startet beziehungsweise
startet den Dienst nach Installation und Upgrade daher ausdrücklich neu.

Das Gastskript verweigert die Ausführung ohne die ausschließlich der Test-VM
übergebene Kernelmarkierung. Es darf nicht als Verwaltungswerkzeug für einen
bestehenden Server verwendet werden.

## Ausgeführter Nachweis vom 22. September 2026

Der vollständige Lauf von **15:52:05 bis 15:53:07 UTC** bestand mit Exitcode 0.
Gast: Debian 12, Kernel `6.1.0-53-amd64`, `systemd 252 (252.39-1~deb12u2)`;
`/proc/1/comm` bestätigte `systemd` als PID 1. Alle zwölf gespeicherten Checks
sind `PASS`:

| Prüfbereich | Tatsächlich beobachtetes Ergebnis |
|---|---|
| Installation und Upgrade | Version 1.0.0 installiert, anschließend 1.1.0 installiert und per dpkg abgefragt |
| systemd-Dienst | Nach beiden Installationen aktiv und aktiviert; MainPID von systemd ermittelt |
| Servicekonto | Tatsächliche Prozess-UIDs entsprechen dem dedizierten Konto und sind nicht root |
| Healthcheck | HTTP 200 nach Installation und nach Upgrade |
| Konfiguration und Daten | Eigene Änderung und Sentinel nach Upgrade und Remove erhalten |
| Remove | Dienst beendet, vorherige MainPID verschwunden und Unitdatei entfernt |

Die unveränderten Eingangsartefakte haben folgende SHA-256-Digests:

```text
auditcore-fixture_1.0.0_all.deb
a0d2b81b9e4693747af7a1594685c319eb2268f69312b3cf92e623fbcc2cc528

auditcore-fixture_1.1.0_all.deb
fdd22ce7d3ce1fb22f72177df77075ee0e0f3f3eae009a0843c7cf22929eab04

Testimage
sha256:3cd529d1ac9d85ecc42d7cc2d32242f7063d736225c8c5935dc8ca7192e6555d

console.log
c5fc1c51d959ecc7b040611ab199f1d80c5a777562af3123eb87b93a772d69e4
```

Die vollständigen lokalen Rohdaten stehen unter
`.auditcore/systemd-validation-lifecycle/`. Frühere fehlgeschlagene
Testumgebungsversuche bleiben in getrennten Verzeichnissen erhalten. Der
bisherige cgroup-Blocker ist damit für die synthetischen Pakete behoben;
eine reale Fachanwendung wurde durch diesen Lauf nicht migriert oder freigegeben.

## Aussagegrenze

Ein bestandener Lauf bestätigt die genannten technischen Prüfungen für exakt
die im Ergebnis gehashten Pakete. Er ersetzt weder anwendungsspezifische
Regressionstests noch Policy-Evaluation, Backup-/Restore-Nachweise oder eine
Produktivfreigabe. `release_authorization` bleibt `NOT_EVALUATED`.
Die bisherigen Docker-Prüfergebnisse bleiben unverändert und erhalten keinen
nachträglich erfundenen systemd-Nachweis. Fehlende VM-Ergebnisse bleiben
`NOT_EXECUTED`; tatsächliche fehlgeschlagene Gastprüfungen liefern `FAIL`.
