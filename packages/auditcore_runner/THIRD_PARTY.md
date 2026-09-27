# Fremde Programme und Abhängigkeiten

## Python-Abhängigkeiten des Pakets

| Paket | Verwendung | Lizenz |
|---|---|---|
| PyYAML ≥ 6.0 | Workflow-Prüfung (Extra `workflows`) | MIT |
| PyJWT[crypto] ≥ 2.8 | GitHub-App-Anmeldung (Extra `github-app`) | MIT; cryptography: Apache-2.0 oder BSD-3-Clause |

Pflichtabhängigkeiten gibt es keine. Der Test `tests/test_lizenzen.py` prüft
die Lizenzen der installierten Extras `github-app` und `workflows` auf
MIT-Verträglichkeit.

## Protokoll-Referenz

| Quelle | Verwendung | Lizenz |
|---|---|---|
| github.com/actions/scaleset (Commit `e6daac7`) | Vorlage für das Protokoll des Backends `scaleset`; in Python nachgebaut, kein Code übernommen | MIT, Text in `LICENSES/actions-scaleset-MIT.txt` |

## Programme im Runner-Image (`data/Dockerfile`)

Separate Programme, die nur als eigener Prozess aufgerufen werden; nichts
davon ist in den Paketcode übernommen oder damit verlinkt. Pins:
`data/werkzeuge/binaer.json` (Binärdateien mit SHA-256), `requirements.txt`
und `requirements-libcst.txt` (Python, je eigene Umgebung), `package.json`
mit `package-lock.json` (Node). Dependabot hält pip und npm aktuell; die
Binärdateien werden mit Version und Prüfsumme gemeinsam angehoben.

### Basis

| Programm | Version | Lizenz | Quelle |
|---|---|---|---|
| GitHub Actions Runner (Basis-Image) | 2.337.0 (Digest gepinnt) | MIT | github.com/actions/runner |
| uv | 0.12.19 (Digest gepinnt) | MIT oder Apache-2.0 | github.com/astral-sh/uv |
| Node.js | 24.21.0 (SHA-256) | MIT (enthaltene Bibliotheken: siehe LICENSE im Archiv) | github.com/nodejs/node |
| Ubuntu-Pakete (Compiler, Pango, Cairo, DejaVu, Liberation, Noto …) | aus dem Basis-Image | jeweilige Paketlizenzen (Schriften u. a. OFL-1.1) | Ubuntu |
| Chrome for Testing (über Playwright) | zu Playwright 1.63.0 | BSD-3-Clause und enthaltene Lizenzen | chromium.googlesource.com |

### Binärdateien (SHA-256 geprüft)

| Programm | Version | Lizenz | Quelle |
|---|---|---|---|
| gitleaks | 8.30.1 | MIT | github.com/gitleaks/gitleaks |
| betterleaks | 1.8.1 | MIT | github.com/betterleaks/betterleaks |
| actionlint | 1.7.12 | MIT | github.com/rhysd/actionlint |
| osv-scanner | 2.6.0 | Apache-2.0 | github.com/google/osv-scanner |
| grype | 0.119.0 | Apache-2.0 | github.com/anchore/grype |
| syft | 1.52.0 | Apache-2.0 | github.com/anchore/syft |
| trivy | 0.74.0 (nur per SHA-256, siehe unten) | Apache-2.0 | github.com/aquasecurity/trivy |
| **Opengrep** | 1.30.0 | **LGPL-2.1** – Lizenztext und Quelle unter `LICENSES/` | github.com/opengrep/opengrep |
| lychee | 0.24.2 | Apache-2.0 oder MIT | github.com/lycheeverse/lychee |
| reviewdog | 0.21.2 | MIT | github.com/reviewdog/reviewdog |
| prek | 0.5.3 | MIT | github.com/j178/prek |

trivy wird ausschließlich über die Prüfsumme einer geprüften Release-Datei
eingebunden, nicht über Tags oder Installationsskripte (Lieferketten-Vorfall
GHSA-69fq-xp46-6x23 / CVE-2026-33634 mit manipulierten Tags und Images).
Opengrep ersetzt Semgrep; das Image enthält keine Semgrep-Regeln, Regeln
kommen aus `.opengrep/` des geprüften Projekts.

### Python-Werkzeuge (je eigene Umgebung)

| Programm | Version | Lizenz |
|---|---|---|
| ruff | 0.16.9 | MIT |
| mypy | 2.3.1 | MIT |
| zizmor | 1.30.1 | MIT |
| pyrefly | 1.3.1 | MIT |
| vulture | 2.16 | MIT |
| deptry | 0.25.1 | MIT |
| import-linter | 2.15 | BSD-2-Clause |
| **codespell** | 2.4.3 | **GPL-2.0-only** – Lizenztext und Quelle unter `LICENSES/` |
| typos | 1.50.3 | MIT oder Apache-2.0 |
| mutmut | 3.8.0 | BSD-3-Clause |
| diff-cover | 10.6.0 | Apache-2.0 |
| ast-grep-cli | 0.45.3 | MIT |
| libcst | 1.9.0 | MIT (Teile PSF-2.0 und Apache-2.0) |

pytest-testmon und pytest-split (beide MIT) gehören in die Testumgebung des
geprüften Projekts und sind nicht im Image.

### Node-Werkzeuge (`/opt/node-tools`)

| Programm | Version | Lizenz |
|---|---|---|
| @playwright/test | 1.63.0 | Apache-2.0 |
| **@axe-core/playwright** (mit axe-core 4.13.0) | 4.13.0 | **MPL-2.0** – Lizenztext und Quelle unter `LICENSES/` |
| @lhci/cli | 0.15.1 | Apache-2.0 |
| typescript | 7.0.2 | Apache-2.0 |
| vitest | 5.0.2 | MIT (Abhängigkeit lightningcss: MPL-2.0, siehe `LICENSES/`) |
| prettier | 3.9.9 | MIT |
| stylelint | 17.15.0 | MIT |
| jscpd | 5.3.2 | MIT |
| knip | 6.38.0 | ISC |
| size-limit, @size-limit/file | 14.0.1 | MIT |
| markdownlint-cli | 0.49.1 | MIT |

Alle übrigen Pakete im Lockfile stehen unter MIT, ISC, Apache-2.0,
BSD-2/3-Clause, 0BSD, MIT-0, BlueOak-1.0.0, CC0-1.0 oder Python-2.0
(argparse). Ohne Lizenzfeld im Lockfile und von Hand geprüft:
parse-cache-control 1.0.1 (BSD-3-Clause), svg-tags 1.0.0 (MIT). Der Test
`tests/test_image_lizenzen.py` prüft Lockfile, Pins und diese Tabelle.

## Copyleft-Programme

GPL-, LGPL- und MPL-lizenzierte Werkzeuge liegen nur als separate,
unveränderte Programme im Image; AGPL-Werkzeuge sind nicht enthalten.
Lizenztexte und Quellverweise: `src/auditcore_runner/data/LICENSES/`, im
Image unter `/usr/share/doc/auditcore-runner/LICENSES/`. Keine kommerziellen
oder nicht frei nutzbaren Werkzeuge im Standard-Image.
