# Sicherheitsmodell

Ein self-hosted Runner führt fremden Code aus (PR-Inhalte). Das Paket geht davon
aus, dass jeder Job feindlich sein kann, und begrenzt, was er erreicht.

## Container

- Ephemer: je Job eine Einmal-Registrierung (JIT) und ein frischer Container
  (`docker run --rm`); nach dem Job wird die Registrierung gelöscht.
- `--cap-drop ALL`, `--security-opt no-new-privileges`, `--pids-limit 4096`,
  CPU-, RAM- und CPU-Anteil-Grenzen aus dem Profil. Der Runner-Nutzer im Image
  ist weder in `sudo` noch in `docker`; kein Docker-Socket, keine Host-Verzeichnisse
  (nur benannte Cache-Volumes).
- Die JIT-Konfiguration liegt als Datei auf tmpfs (`$XDG_RUNTIME_DIR`, Verzeichnis
  0700) und wird eingebunden – sie steht nicht in `docker inspect`.

## Netz

Das eigene Docker-Netz (`netz.name`, eigenes Subnetz und eigene Brücke) wird per
root-Skript gesperrt (`~/.config/auditcore-runner/root/firewall-installieren.sh`,
das Paket führt nichts mit root aus): keine Verbindungen in private Netze
(RFC 1918), CGNAT/Tailscale (100.64.0.0/10), Link-Local und zum Host selbst;
Internet bleibt erlaubt. Ist `sperre_pflicht` gesetzt, registriert der Supervisor
erst, wenn die Sperre aktiv ist. Eine Positivliste (nur GitHub, Paketquellen) ist
für eine spätere Version vorgesehen.

## Zugangsdaten

Das Profil enthält nur Pfade (`auth.token_datei`, `auth.app_schluessel_datei`).
Empfohlen ist eine GitHub App mit minimalen Rechten (Repository
„Administration: write“ nur für Runner-Registrierung, „Actions: read“) oder ein
fein granulares Token für genau ein Repository. Das Token bleibt auf dem Host;
Container sehen es nie.

## Überwachung

`runner status` listet registrierte Runner, deren Name keinem eigenen Rechner
gehört (`unbekannte_runner`, Metrik `auditcore_runner_unknown_registered`) –
ein bekanntes Angriffsmuster ist das Registrieren fremder Runner mit gestohlenen
Tokens. Die Runner-Version im Image prüft `image pruefen` (Mindestversion,
30-Tage-Frist nach einem neuen Release).

## Workflows

`auditcore-runner workflows pruefen` ruft zizmor und actionlint auf (wenn
installiert) und prüft zusätzlich: Jobs, die auf einem self-hosted Runner landen
können, brauchen in PR-Workflows einen Fork-Schutz; Secrets (außer
`GITHUB_TOKEN`) und Dependabot-PRs nur auf gehosteten Runnern.

## Lokale Oberfläche

Bindet an 127.0.0.1. Änderungen nur von Loopback, mit Kopfzeile
`X-Auditcore-Runner: 1` und Loopback-`Host` (Schutz vor DNS-Rebinding); eine
zusätzliche Adresse (`ui --lesend-an`) ist ausschließlich lesend. CSP ohne
fremde Quellen.
