# Fremde Programme und Abhängigkeiten

## Python-Abhängigkeiten des Pakets

| Paket | Verwendung | Lizenz |
|---|---|---|
| PyYAML ≥ 6.0 | Workflow-Prüfung (Pflicht) | MIT |
| PyJWT[crypto] ≥ 2.8 | GitHub-App-Anmeldung (Extra `github-app`) | MIT; cryptography: Apache-2.0 oder BSD-3-Clause |

Der Test `tests/test_lizenzen.py` prüft die Lizenzen der installierten
Laufzeitabhängigkeiten auf MIT-Verträglichkeit.

## Programme im Runner-Image (`data/Dockerfile`)

Separate Programme, die nur aufgerufen werden; nichts davon ist in den
Paketcode übernommen.

| Programm | Version | Lizenz | Quelle |
|---|---|---|---|
| GitHub Actions Runner (Basis-Image) | 2.337.0 (Digest gepinnt) | MIT | github.com/actions/runner |
| uv | 0.12.19 (Digest gepinnt) | MIT oder Apache-2.0 | github.com/astral-sh/uv |
| ruff | 0.16.9 | MIT | github.com/astral-sh/ruff |
| mypy | 2.3.1 | MIT | github.com/python/mypy |
| zizmor | 1.30.1 | MIT | github.com/zizmorcore/zizmor |
| gitleaks | 8.30.1 (SHA-256 geprüft) | MIT | github.com/gitleaks/gitleaks |
| actionlint | 1.7.12 (SHA-256 geprüft) | MIT | github.com/rhysd/actionlint |
| Ubuntu-Pakete (Compiler, Pango, Cairo, Schriften …) | aus dem Basis-Image | jeweilige Paketlizenzen | Ubuntu |

Keine kommerziellen oder nicht frei nutzbaren Werkzeuge im Standard-Image.
Werkzeuge mit Copyleft-Lizenz (etwa GPL oder LGPL) kommen nur als separate
Programme mit Lizenztext unter `LICENSES/` und Quellverweis hinzu.
