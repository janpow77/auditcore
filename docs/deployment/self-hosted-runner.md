# Self-hosted CI-Runner

Die CI von auditcore kann auf eigenen Rechnern mit ephemeren Runnern laufen.
GitHub-Runner bleiben der Rückfallweg und der Ort für Fork-PRs, Dependabot und
Läufe, die Docker brauchen. Runner-Verwaltung, Skalierung und Prüfbank liefert
das Paket [`auditcore_runner`](../../packages/auditcore_runner); `ci/runner/`
bleibt nur als Kompatibilitätsschicht für bestehende Installationen.

## Neuen Rechner anbinden in 5 Befehlen

Voraussetzungen: Linux mit systemd, Docker, `jq` und Zugangsdaten – empfohlen
eine GitHub App (`~/.config/auditcore-runner/github-app.json`), sonst ein fein
granulares Token (`~/.config/auditcore-runner/github-token`); `gh auth login`
nur für einen Einzelrechner (siehe Paket-Doku).

```bash
uv tool install auditcore_runner --index-url https://janpow77.github.io/auditcore/simple/
auditcore-runner profil erkennen --ziel janpow77/auditcore --speichern
auditcore-runner runner install --trockenlauf     # Units, Image, Netz und Befehle prüfen
auditcore-runner runner install
sudo bash ~/.config/auditcore-runner/root/firewall-installieren.sh   # einmalig: Netzsperre
```

Grenzen, Labels, GPUs, Prioritäten und die Soll-Quelle (statisch, lokaler
Autoskalierer oder externer Regler) stehen im Profil
(`~/.config/auditcore-runner/profil.json`, Referenz
[`docs/konfiguration.md`](../../packages/auditcore_runner/docs/konfiguration.md));
Einstellungen über `auditcore-runner ui` oder `profil anwenden`.

## Architektur

- Je Klasse (frei benennbar, Vorlage `cpu`, `cpu-gross`, `gpu-16gb`, `gpu-8gb`) eine systemd-User-Unit
  `auditcore-runner-<klasse>@<n>`; jede Instanz holt je Job eine
  Einmal-Registrierung (JIT) und startet einen frischen Container aus dem
  Runner-Image des Pakets.
- Vor jeder Registrierung liest der Supervisor Profil und Soll neu: Änderungen
  wirken ab dem nächsten Job, laufende Jobs werden nie abgebrochen,
  überzählige Instanzen ruhen.
- GPU-Runner wählen die Karte je Job nach freiem VRAM; nutzt jemand die Karte
  interaktiv, wird sie sofort geräumt.

## Sicherheitsmodell

Siehe [`docs/sicherheit.md`](../../packages/auditcore_runner/docs/sicherheit.md):
ephemere Container ohne Capabilities, Docker-Socket und Host-Verzeichnisse,
eigenes Netz ohne Zugriff auf private Netze und den Host, JIT-Konfiguration als
Datei, Tokens nur auf dem Host, Warnung bei unbekannten registrierten Runnern.
Fork-PRs laufen nie auf eigenen Runnern; `auditcore-runner workflows pruefen`
prüft das für alle Workflows.

## Umschalten

Die Repo-Variable `AUDITCORE_RUNNER` steuert, wohin die Jobs gehen:

```bash
gh variable set AUDITCORE_RUNNER --repo janpow77/auditcore --body '["self-hosted","auditcore"]'
gh variable delete AUDITCORE_RUNNER --repo janpow77/auditcore   # zurück auf GitHub
```

## Bestehende Installation (`ci/runner`)

```bash
ci/runner/install.sh            # veraltet; Image bauen, Instanzen installieren
ci/runner/install.sh --uninstall
```

Umstieg: `auditcore-runner runner install` meldet alte Units `auditcore-runner@N`;
nach dem Umstieg `ci/runner/install.sh --uninstall`, wenn gerade kein Job läuft.
