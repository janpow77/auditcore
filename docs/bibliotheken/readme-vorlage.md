# README-Vorlage für Bibliotheken (verbindlich)

Jedes Paket unter `packages/` (Python) und `packages-js/` (npm) beschreibt sich
in seiner `README.md` nach dieser Vorlage. Die Prüfung ist Code, nicht
Empfehlung: `tests/test_readmes.py` (Workflow `quality`) und
`scripts/js/check-readme-snippets.mjs` (Workflow `js-packages`) lassen den
Build scheitern, wenn ein Pflichtabschnitt fehlt, der Schnellstart nicht läuft
oder ein generierter Block veraltet ist. Neue Pakete müssen die Prüfung von
Anfang an bestehen; die Liste
[`readme-offen.json`](readme-offen.json) enthält nur noch nicht überarbeitete
Bestandspakete und darf nur kürzer werden.

Grundsätze:

- **Nichts erfinden.** Inhalte stammen aus Code, Docstrings, `docs/`,
  `provenance.json`, `pyproject.toml`/`package.json` und dem CHANGELOG.
  Was nicht belegt ist, steht nicht in der README (oder ausdrücklich als offen).
- **Deutsch mit echten Umlauten** (ä ö ü ß). VerwK statt VKO,
  „Feststellungen“ statt „Findungen“. Die Prüfung meldet ASCII-Ersatz wie
  „fuer“ oder „Pruefung“ außerhalb von Code.
- **Kurz.** Details gehören nach `docs/`; die README verlinkt dorthin.
- Die Abschnitte stehen als Überschriften der Ebene 2 (`## …`) **genau mit
  diesen Namen und in dieser Reihenfolge**. Weitere eigene Abschnitte dürfen
  dazwischen stehen.

## Python-Pakete (`packages/<paket>/README.md`)

| Abschnitt | Inhalt | Geprüft |
|---|---|---|
| `# <distribution>` | Titel = Distributionsname, z. B. `# auditcore_geo` | – |
| `## Zweck` | **Erster Absatz: ein Satz** (höchstens 240 Zeichen), der im [Paketkatalog](uebersicht.md) erscheint. Danach 1–2 Sätze: für wen (welche Anwendungen, welche Rolle), was ausdrücklich nicht dazugehört. | nicht leer, Katalogzeile ≤ 240 Zeichen |
| `## Installation` | pip über den Paketindex, Direkt-URL mit `sha256`, APT, alle Extras (siehe Muster unten) | Index-URL, `--index-url`, `#sha256=`, `python3-<paket>`, jedes Extra außer `dev` als `[extra]` |
| `## Schnellstart` | Ein lauffähiges Beispiel nur mit Pflichtabhängigkeiten, das etwas Fachliches zeigt und sein Ergebnis mit `assert` bzw. `>>>`-Ausgabe belegt | Mindestens ein ```` ```python ```` oder ```` ```pycon ````-Block; **wird ausgeführt** |
| `## API-Überblick` | Generierter Block (öffentliche Namen aus `__all__` mit erster Docstring-Zeile, öffentliche Module). Davor oder danach höchstens kurze Hinweise zur Gliederung. | Markierungen vorhanden, Block aktuell |
| `## Profile und Konfiguration` | Benannte Profile, Standardwerte, Umgebungsvariablen, Laufparameter; „Keine“ mit Begründung, wenn es nichts gibt | nicht leer |
| `## Herkunft und Charakterisierung` | Aus welchen Anwendungen/Repositories (Commit/Pfad laut `provenance.json`), wie charakterisiert (Fixture, Fallzahl), ob legacy-exakt oder Neuimplementierung | nicht leer |
| `## Bewusste Verhaltensabweichungen` | Kurzfassung und Link auf `docs/behavior-changes.md`, falls vorhanden; sonst „Keine“ und warum | Link Pflicht, wenn die Datei existiert |
| `## Abhängigkeiten` | Pflichtabhängigkeiten mit Version, Extras und ihre Drittpakete, Python-Version; was bewusst nicht Abhängigkeit ist | jede Pflichtabhängigkeit genannt |
| `## Sicherheit und Datenschutz` | Netzwerkzugriffe, personenbezogene Daten, Geheimnisse, Eingabevalidierung, Grenzen (z. B. „keine Freigabe“) | nicht leer |
| `## Lizenz und Herkunftsnachweis` | Lizenz, Verweis auf `LICENSE`, `NOTICE`, `provenance.json`, Freigabe des Rechteinhabers | `LICENSE` und `provenance.json` genannt |
| `## Änderungen` | Link auf `CHANGELOG.md` | Link vorhanden, CHANGELOG hat Überschrift `## <aktuelle Version> …` |

### Muster Installation (Python)

````markdown
## Installation

Aus dem Paketindex von auditcore (PEP 503, jede Datei mit SHA-256 verlinkt):

```bash
python -m pip install 'auditcore_beispiel==1.2.3' \
  --index-url https://janpow77.github.io/auditcore/simple/
```

Hashgebunden in einer `requirements.txt` (Direkt-URL und `sha256` stehen im
Index unter `https://janpow77.github.io/auditcore/simple/auditcore-beispiel/`):

```text
auditcore_beispiel @ https://github.com/janpow77/auditcore/releases/download/v<release>/auditcore_beispiel-1.2.3-py3-none-any.whl#sha256=<sha256>
```

Debian/Ubuntu über die signierte APT-Quelle des Releases
([Einrichtung](../../docs/deployment/package-feed.md)):

```bash
sudo apt-get install python3-auditcore-beispiel
```

Extras: `[pdf]` – PDF-Ausgabe über reportlab; `[dev]` – Test- und Prüfwerkzeuge.
````

`--index-url` statt `--extra-index-url` verhindert, dass ein gleichnamiges
fremdes Paket von PyPI geladen wird. Ist die aktuelle Version noch nicht
veröffentlicht, nennt der Abschnitt die zuletzt veröffentlichte Version oder
sagt es ausdrücklich.

### Muster Schnellstart (Python)

````markdown
## Schnellstart

```python
from auditcore_beispiel import berechne

ergebnis = berechne([1, 2, 3])
assert ergebnis.summe == 6
```

```pycon
>>> ergebnis.summe
6
```
````

Alle ```` ```python ````-Blöcke des Abschnitts laufen nacheinander in einem
gemeinsamen Namensraum, ```` ```pycon ````-Blöcke werden mit `doctest`
(`ELLIPSIS`, `NORMALIZE_WHITESPACE`) gegen diesen Namensraum geprüft. Der
Lauf nutzt nur die Quellen unter `packages/*/src` und die Standardbibliothek –
Beispiele mit Extras stehen in einem eigenen Abschnitt oder erhalten
`no-run` in der Info-Zeile (```` ```python no-run ````). Kein Netzwerk, keine
Dateien außerhalb eines temporären Verzeichnisses.

Lokal prüfen:

```bash
PYTHONPATH=$(ls -d packages/*/src | paste -sd:) \
  python scripts/docs/readme_snippets.py packages/<paket>/README.md
python scripts/docs/readme_check.py packages/<paket>
```

## npm-Pakete (`packages-js/<paket>/README.md`)

| Abschnitt | Inhalt | Geprüft |
|---|---|---|
| `# @auditcore/<paket>` | Titel = Paketname | – |
| `## Zweck` | wie Python (erster Absatz = Katalogzeile) | wie Python |
| `## Installation` | `npm install @auditcore/<paket>` als Standardweg, Tarball-URL aus dem Release (`npm install @auditcore/<paket>@<Release-URL>.tgz`) als Alternative ohne Registry, Abhängigkeitshülle, Peer-Abhängigkeiten, CSS-Import, Verweis auf [frontend-installation.md](../deployment/frontend-installation.md), npm-Workspace im Repository | `npm install <name>` |
| `## Schnellstart` | Ein ```` ```ts ````- oder ```` ```tsx ````-Beispiel | **wird gegen die gebauten Typen typgeprüft** (strict, `noUncheckedIndexedAccess`); ```` ```ts run ```` wird zusätzlich in Node ausgeführt |
| `## Einbindung` | Nutzung als Vue-Plugin/-Komponente, als Web Component (`<flowaudit-…>`) und aus React, soweit das Paket es anbietet | „Vue“ bei Vue-Abhängigkeit, „Web Component“ bei Export `./elements`, „React“ bei React-Abhängigkeit |
| `## API-Überblick` | Generierter Block: Exporte je Einstiegspunkt mit erster JSDoc-Zeile, Web Components, **Props und Ereignisse** der Vue-Komponenten (aus `defineProps`/`defineEmits`) | Markierungen vorhanden, Block aktuell |
| `## Konfiguration` | Optionen, Theming (CSS-Variablen), Sprache, Ports | nicht leer |
| `## Herkunft und Charakterisierung` | Neu oder übernommen, Paritätsnachweis (z. B. gemeinsame Fixtures mit dem Python-Paket), `PROVENANCE.md` | nicht leer |
| `## Abhängigkeiten` | `dependencies` und `peerDependencies` mit Version | jede genannt |
| `## Sicherheit und Datenschutz` | DOM-/HTML-Ausgabe (Escaping), Netzwerkzugriffe (`fetch`), gespeicherte Daten | nicht leer |
| `## Lizenz und Herkunftsnachweis` | MIT, `LICENSE`, ggf. `PROVENANCE.md` | `LICENSE` genannt |
| `## Änderungen` | Link auf `CHANGELOG.md` im Paketverzeichnis | wie Python |

Lokal prüfen (nach `npm ci` und `npm run build`):

```bash
node scripts/js/check-readme-snippets.mjs
python scripts/docs/api_overview.py --check --js
```

## Generierte Blöcke

| Block | Erzeuger | Prüfung |
|---|---|---|
| `<!-- api-overview:start … -->` … `<!-- api-overview:end -->` in jeder Paket-README | `python scripts/docs/api_overview.py --write [paket …]` | Python: `tests/test_readmes.py`; npm: Workflow `js-packages` |
| `<!-- paketkatalog:start … -->` … `<!-- paketkatalog:end -->` in `README.md` und [`uebersicht.md`](uebersicht.md) | `python scripts/docs/catalog.py --write` | `tests/test_readmes.py` |

Der Katalog liest Version und Abhängigkeiten aus `pyproject.toml` bzw.
`package.json`, die Katalogzeile aus dem ersten Absatz von „Zweck“ und den
Status aus `provenance.json` (`classification`, `characterization`). Nach jeder
Versionsänderung und jeder Änderung des Zweck-Absatzes beide Erzeuger
ausführen und das Ergebnis mit committen.

## Neues Paket anlegen

1. README nach dieser Vorlage schreiben, Markierungen für den API-Block setzen.
2. `CHANGELOG.md` mit `## <version> – <datum>` anlegen.
3. `python scripts/docs/api_overview.py --write packages/<paket>` und
   `python scripts/docs/catalog.py --write` ausführen.
4. `pytest tests/test_readmes.py -k <paket>` (npm zusätzlich die beiden
   Befehle oben).

Das Paket nicht in `readme-offen.json` eintragen – die Liste ist nur für den
Bestand vom 25.09.2026.
