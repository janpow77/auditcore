# Konfigurationsreferenz

Das Profil liegt unter `~/.config/auditcore-runner/profil.json` (JSON). Maßgeblich
ist das Schema aus `auditcore-runner profil schema`; ältere Fassungen werden beim
Lesen migriert (`schema: auditcore-runner/profil/<version>`, derzeit 3; Version 3 hat frei
benennbare Klassen mit `art`, die Migration leitet `art` aus dem alten Namen,
`vram_mb` und den zugeordneten Karten ab).
Änderungen immer über `auditcore-runner profil anwenden` oder die Oberfläche –
beide validieren gleich, erhöhen `version` und schreiben `aenderung`.

| Bereich | Feld | Bedeutung | Standard |
|---|---|---|---|
| Kopf | `version`, `aenderung.{zeit,quelle,wer}` | fortlaufende Version, letzte Änderung (`lokal` oder `flow-agent`) | 0 |
| | `sync` | nur Anzeige: `aus` oder `flow-agent` (zentral mitgepflegt) | `aus` |
| | `rechner` | Name; Präfix der Runner-Namen | Hostname |
| `ziel` | `art`, `name` | `repo` (`<owner>/<repo>`) oder `org` | – |
| | `runner_gruppe`, `repos_beobachten`, `bekannte_runner` | Runner-Gruppe; bei `org` Repos für die Warteschlange; Namenspräfixe anderer eigener Rechner | 1, [], [] |
| `auth` | `art` | `app` (GitHub App, empfohlen), `pat` (fein granulares Token) oder `gh` (gh-Anmeldung, nur Einzelrechner) | Vorschlag: `app`, wenn `github-app.json` im Konfigurationsverzeichnis liegt, sonst `pat`, wenn `github-token` dort liegt, sonst `gh` |
| | `token_datei`, `app_id`, `app_schluessel_datei`, `installation_id` | nur Pfade und IDs, nie Geheimnisse | – |
| | `image`, `backend` | Runner-Image; Backend `jit` (REST-JIT je Job) oder `scaleset` (Runner-Scale-Set, siehe [backends.md](backends.md)) | `auditcore-runner:local`, `jit` |
| | `gpu_zugriff` | `cdi` (`--device nvidia.com/gpu=<UUID>`) oder `gpus` (`--gpus device=<UUID>`, ältere Docker) | `cdi` |
| `scale_set` | `name_praefix`, `runner_gruppe` | nur Backend `scaleset`: Scale-Set je Klasse `<praefix>-<klasse>` (leer = Rechnername); Runner-Gruppe (Repositories: `default`) | `""`, `default` |
| `reserve` | `cpus`, `speicher_gb` | für den Rechner freigehalten; Summe aller Klassen × max muss darunter bleiben | 4, 12 |
| `netz` | `name`, `subnetz`, `bruecke`, `aktiv`, `sperre_pflicht` | eigenes Docker-Netz; Supervisor wartet auf die Netzsperre, wenn Pflicht | `auditcore-ci`, `172.30.250.0/24` |
| | `egress` | `aus` (Internet offen, nur private Netze gesperrt) oder `allowlist` (nur die Ziele unten) | `aus` |
| | `egress_hosts`, `egress_github_meta`, `egress_ports` | Hostnamen (GitHub, PyPI, npm, Container-Registrys), Bereiche aus `api.github.com/meta` (`api`, `web`, `git`, `packages`, `actions` …), erlaubte TCP-Ports | siehe `profil schema`, 80/443 |
| `soll_quelle` | `art`, `datei` | `statisch`, `lokal` oder `datei` (externer Regler) | `statisch`, `~/.config/auditcore-runner/soll.json` |
| `klassen.<k>` | `art`, `aktiv`, `cpus`, `speicher_gb`, `min_instanzen`, `max_instanzen` | Grenzen je Klasse; Name frei (a–z, 0–9, Bindestrich, ≤ 31 Zeichen), Vorlage `cpu`, `cpu-gross`, `gpu-16gb`, `gpu-8gb`; `art` `cpu` oder `gpu` (GPU-Runner bekommen je Job eine Karte) | – |
| | `leise_max`, `vram_mb`, `labels`, `cpu_shares`, `nice`, `io_gewicht`, `uv_cache_volume` | Maximum im Leise-Modus (-1 = wie max), VRAM-Bedarf je GPU-Runner, Runner-Labels, Priorität | – |
| `gpus[]` | `index`, `uuid`, `name`, `vram_mb`, `erlaubt`, `klasse` | erlaubte Karten; welche genutzt wird, entscheidet sich je Job | erkannt |
| `prioritaeten[]` | `klasse`, `rang`, `verdraengbar`, `min` | Rangfolge (1 = höchste) von Klassen und Prüfprofilen; bei knapper Kapazität werden verdrängbare Klassen mit hohem Rang zuerst bis `min` gesenkt | [] |

## Skalierung (`skalierung`, Soll-Quelle `lokal`)

| Feld | Bedeutung | Standard |
|---|---|---|
| `vorrang_interaktiv` | interaktive Nutzung (Eingaben, gesperrt/entsperrt, GameMode) hat Vorrang | aus |
| `leerlauf_minuten`, `anteil_bei_nutzung` | ab wann „untätig“; Anteil der Instanzen bei Nutzung (mindestens 1) | 10, 0,25 |
| `interaktive_karten`, `interaktive_karten_leerlauf_minuten` | Kartenindizes, die bei Nutzung nicht vergeben werden | [], 15 |
| `ram_frei_min_gb`, `swap_einlagerung_max_s`, `swap_sperre_gb` | Speichernot: wenig freier RAM oder aktives Einlagern (Seiten/s); belegter Swap nur optional (0 = aus) | 4, 256, 0 |
| `last_je_kern_max`, `temperatur_max_c` | Last- und Temperaturgrenze | 0,8, 85 |
| `volllast_von`, `volllast_bis` | Zeitfenster ohne Nutzungsbegrenzung; gleiche Werte = kein Fenster | 0, 0 |
| `freie_reserve`, `haltezeit_s`, `intervall_s` | freie Runner über dem Bedarf; Haltezeit vor dem Absenken; Messintervall | 1, 300, 30 |
| `thermik.{aktiv,url,felder,leise_wert,abstand_c}` | optionale HTTP-JSON-Quelle; `felder.drosselung_aktiv`/`temperatur`/`grenze` sind Pfadlisten (`a.b`, `liste[*].feld`), `felder.modus` ein Pfad | aus |
| `gpu_dienste_teilen` | Prozessnamen-Muster, mit denen GPU-Runner eine Karte teilen; alle anderen Prozesse gelten als Nutzer | [] |

Druck-, Thermik- und Nutzer-Vorrang-Grenzen wirken sofort; alle anderen
Absenkungen erst nach der Haltezeit. Mindestzahlen (`min_instanzen`,
`prioritaeten[].min`) gelten nur, solange kein dringender Grund dagegen spricht.
