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
erst, wenn die Sperre aktiv ist.

**Egress-Allowlist** (`netz.egress: allowlist`): zusätzlich sind nur die Ziele
aus `egress_hosts` (per DNS aufgelöst) und die GitHub-Bereiche aus
`api.github.com/meta` auf den Ports `egress_ports` erreichbar; alles andere wird
abgelehnt. Das erzeugte root-Skript füllt ein ipset (`auditcore-ci-egress`),
ein root-Zeitgeber (`auditcore-ci-egress.timer`, alle 30 Minuten) löst neu auf;
eine leere Auflösung ersetzt die alte Liste nicht. Braucht `ipset`, `jq` und
`curl` auf dem Host. Grenzen: CDN-Adressen wechseln (bis zur nächsten
Auflösung kann ein Download scheitern); Ziele, die sich eine Adresse mit
erlaubten Hosts teilen, sind mit erreichbar. DNS läuft über den Docker-Resolver
auf dem Host und ist nicht eingeschränkt.

## GPUs

GPU-Runner bekommen je Job genau eine Karte per CDI
(`--device nvidia.com/gpu=<UUID>`, einmalig `nvidia-ctk cdi generate`). Die Wahl
(`gpu waehlen --platz <klasse-n>`) reserviert die Karte, bis der Container läuft;
mehrere Runner teilen eine Karte nach VRAM. Nutzt ein Mensch die Karte oder
setzt ein Regler `nutzer_vorrang`/`karten_gesperrt`, wird der Container sofort
gestoppt (einzige Ausnahme von „laufende Jobs bleiben“).

## Zugangsdaten

Das Profil enthält nur Pfade (`auth.token_datei`, `auth.app_schluessel_datei`).
Empfohlen ist eine GitHub App mit minimalen Rechten (Repository
„Administration: write“ nur für Runner-Registrierung, „Actions: read“) oder ein
fein granulares Token für genau ein Repository. Das Token bleibt auf dem Host;
Container sehen es nie. Beim Backend `scaleset` gehen Tokens nur per TLS an
`api.github.com` und Hosts unter `actions.githubusercontent.com`; andere
Adressen in Antworten werden abgelehnt.

## Überwachung

`runner status` listet alle registrierten Runner (alle Seiten der API), deren
Name keinem eigenen Rechner gehört (`unbekannte_runner`, Details mit Labels und
passender Klasse in `unbekannte_runner_details`, Metriken
`auditcore_runner_unknown_registered` und `…_unknown_matching_class`) – ein
bekanntes Angriffsmuster ist das Registrieren fremder Runner mit gestohlenen
Tokens, die dann eigene Jobs abgreifen. Jede neu auftauchende Registrierung
meldet der Status-Zeitgeber einmal als `WARNUNG` im Journal;
`runner status --streng` endet dann mit Exit 4 (für Überwachung). Die Runner-Version im Image prüft `image pruefen` (Mindestversion,
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
