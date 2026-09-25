# CI-Runner auf der NUC

Die CI von auditcore läuft überwiegend auf ephemeren Runnern auf der NUC. GitHub-Runner bleiben als Rückfallweg und für Läufe, die Docker brauchen.

## Architektur

- `ci/runner/supervisor.sh` holt je Job eine Einmal-Registrierung (JIT, `generate-jitconfig`) und startet dafür einen frischen Container aus `ci/runner/Dockerfile`. Nach dem Job wird der Container verworfen.
- Das GitHub-Token (`gh auth`) bleibt auf dem Host. Der Container erhält nur die einmal gültige JIT-Konfiguration.
- systemd-User-Units `auditcore-runner@1..6` halten sechs Instanzen bereit. Sie starten nach einem Neustart der NUC automatisch (Linger ist aktiv).

## Sicherheitsmodell

- Container: `--cap-drop ALL`, `no-new-privileges`, kein Docker-Socket, kein Host-Netz, keine Host-Verzeichnisse. Der Runner-Nutzer ist nicht in `sudo` oder `docker`.
- Grenzen je Container: 3 CPUs, 8 GB RAM, 4096 Prozesse. `--cpu-shares 512`, damit die Dienste der NUC Vorrang behalten.
- Cache-Volumes (Werkzeuge, pip, npm) gibt es je Instanz getrennt, damit sich ein vergifteter Cache nicht über alle Instanzen verbreitet.
- Fork-PRs laufen nie auf der NUC. Die Workflows leiten sie auf `ubuntu-latest`, und die Repo-Einstellung verlangt eine Freigabe für Workflows aus Forks.
- Läufe, die Docker brauchen (die Python-3.12-Beine mit APT- und Lebenszyklus-Test), bleiben auf `ubuntu-latest`.

## Umschalten

Die Repo-Variable `AUDITCORE_RUNNER` steuert, wohin die Jobs gehen:

```bash
# NUC
gh variable set AUDITCORE_RUNNER --repo janpow77/auditcore --body '["self-hosted","nuc","auditcore"]'
# zurück auf GitHub, etwa wenn die NUC ausfällt
gh variable delete AUDITCORE_RUNNER --repo janpow77/auditcore
```

Ist die NUC aus, warten die Jobs auf einen Runner. Dann die Variable löschen.

## Installation und Betrieb

```bash
ci/runner/install.sh            # Image bauen, 6 Instanzen installieren und starten
ci/runner/install.sh 4          # Anzahl ändern
ci/runner/install.sh --uninstall
systemctl --user status 'auditcore-runner@*'
journalctl --user -u 'auditcore-runner@1' -f
```

Bei einer neuen Runner-Version den Digest im Dockerfile anheben und `install.sh` erneut ausführen.
