# Bibliotheken mit pip oder APT installieren

Die Plattformbibliothek `auditcore` enthält die Werkzeuge zur Herstellung und
Pflege weiterer, fachlich abgegrenzter Bibliotheken. Eigenständige Fachpakete wie
`auditcore_dummygenerator` können im selben Repository gebaut werden. Anwendungen
bleiben in ihren eigenen Repositories und deklarieren ihre tatsächlichen
Bibliotheksabhängigkeiten. Ein gemeinsames Repository erzwingt keine gemeinsame
Python-Distribution.

## pip und requirements.txt

Ein fertiges Wheel wird in einem freigegebenen Paketindex oder einem Wheel-Verzeichnis
bereitgestellt. Für das bereits gebaute Plattformwheel funktioniert beispielsweise:

```text
# requirements.txt
--no-index
--find-links /srv/wheelhouse
auditcore==0.1.0
```

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -I -c 'from auditcore.reporting import get_number_format; print(get_number_format("Betrag"))'
```

Das Wheel-Verzeichnis muss auch die freigegebenen Wheels aller Pflichtabhängigkeiten
enthalten. Für reproduzierbare Releases werden Versionen und Wheel-SHA256-Hashes im
Requirements-Lock festgeschrieben und mit `pip install --require-hashes` geprüft.
Für ein tatsächlich veröffentlichtes Fachpaket lautet die entsprechende Abhängigkeit
beispielsweise `auditcore_dummygenerator==<freigegebene Version>`; dieses Beispiel ist
keine Aussage, dass das Fachpaket bereits existiert oder auf PyPI veröffentlicht wurde.
`auditcore-dummygenerator` und `auditcore_dummygenerator` sind normalisierte Schreibweisen
desselben Python-Distributionsnamens; der Importname verwendet Unterstriche.

## Debian-Paket aus dem gleichen Wheel

Der Builder unterstützt `auditcore` sowie eigene Distributionen der Form
`auditcore_<fachname>`. Jede Distribution besitzt ihren gleichnamigen Python-Importordner;
fremde Top-Level-Pakete werden abgelehnt. Metadaten, Wheelname, Pythonversion, Lizenzangaben,
RECORD-Dateiliste und SHA256-Prüfsummen werden vor dem Packen kontrolliert.
Aktuell werden reine `py3-none-any`-Wheels für Python >=3.11 mit stabilen numerischen
Versionen unterstützt. Native Erweiterungen und andere Pythonanforderungen benötigen eine bewusste Erweiterung
des Packagingvertrags. MIT, Apache-2.0 und BSD-2/-3-Clause werden als deklarierte
Lizenzausdrücke erkannt; das ersetzt keine Prüfung der Quellprovenienz. Andere oder
unbekannte Lizenzen blockieren standardmäßig den Build. Ausschließlich für lokale
Tests erlaubt `--allow-unreviewed-license` einen Build mit mitgelieferter Lizenz-
oder NOTICE-Datei und ehrlichem Status `license_status: REVIEW_REQUIRED`,
`release_authorization: REVIEW_REQUIRED`, `publication_status: BLOCKED`.
Der Builder erfindet keine Lizenzgewährung und veröffentlicht keine Pakete.

```bash
python scripts/build_library_deb.py dist/auditcore-0.1.0-py3-none-any.whl \
  --output dist/library \
  --source-date-epoch "$(git show -s --format=%ct HEAD)" \
  --maintainer 'Verantwortlicher Name <verantwortlich@example.org>'
```

Das Ergebnis heißt `python3-auditcore_0.1.0-1_all.deb`. Ein Wheel
`auditcore_dummygenerator-1.2.3-py3-none-any.whl` ergibt entsprechend
`python3-auditcore-dummygenerator_1.2.3-1_all.deb`. Das ist die Namensabbildung,
kein Nachweis einer fachlichen Implementierung.

Auf einem Debian-Zielsystem mit Python >=3.11:

```bash
sudo apt install ./python3-auditcore_0.1.0-1_all.deb
/usr/bin/python3 -I -c 'import auditcore; print(auditcore.__file__)'
auditcore-quality --help
```

Module liegen unter `/usr/lib/python3/dist-packages`; CLI-Skripte verwenden
`/usr/bin/python3`. Der Zielserver benötigt weder pip noch Compiler, Node, Poetry,
uv oder PyPI-Zugriff. Die Maintainer-Skripte rufen ausschließlich Debians `py3compile`
bzw. `py3clean` zur Bytecode-Verwaltung auf. Keine Paketdownloads in `postinst`.

Pflichtabhängigkeiten im Wheel werden nie still weggelassen. Jede vollständige
`Requires-Dist`-Zeichenfolge benötigt eine explizit geprüfte Debianabbildung:

```json
{"requests>=2.30": "python3-requests (>= 2.30)"}
```

Diese JSON-Datei wird mit `--dependency-mapping debian-dependencies.json` übergeben.
Der Verantwortliche prüft, dass das Debianpaket die Pythonanforderung tatsächlich
erfüllt und in den Zielrepositories verfügbar ist. Unbekannte, zusätzliche oder
fehlende Abbildungen blockieren den Build. Optionale Extras werden im Manifest als
nicht mitgeliefert ausgewiesen. Insbesondere enthält das Plattform-Debianpaket keine
optionalen Ruff-/Mypy-/Build-Werkzeuge; die Kernbibliothek hat keine Pflichtdependencies.

Eine normale isolierte venv sieht Debian-Systembibliotheken **nicht** automatisch.
Eine Anwendung wählt daher entweder pip-Abhängigkeiten in ihrer eigenen venv oder
Debian-Systempython und `Depends: python3-auditcore-<fachname>`. Ein bewusstes
`venv --system-site-packages` ist möglich, bindet die Anwendung aber an Systempakete.

Für die Installation allein per Paketname müssen signierte APT-Metadaten mit dem
vorhandenen `AptRepository`-Builder erstellt und ein freigegebenes Repository beim
Consumer eingerichtet werden. Es wurde kein öffentliches APT-Repository publiziert.
Ein Bibliothekspaket erteilt keine Anwendungsfreigabe und installiert keinen Dienst.

## Tatsächlich ausgeführter technischer Nachweis

Das vorhandene Plattformwheel `auditcore-0.1.0-py3-none-any.whl` wurde zum echten
Debianpaket gebaut und in einem isolierten Debian-Bookworm-Container mit
`--network none` über `apt-get install /packages/python3-auditcore_0.1.0-1_all.deb`
installiert. Systempython 3.11.2 importierte `auditcore` und `auditcore.reporting`
mit `-I` nachweislich aus `/usr/lib/python3/dist-packages`; alle fünf CLI-Hilfeaufrufe
funktionierten. Anschließendes `apt-get remove` entfernte auch erzeugten Bytecode;
ein isolierter Import fand das Paket danach nicht mehr.

Lokale Nachweise: `.auditcore/library-package/container-test.log`,
`installation-evidence.json` und das Buildmanifest mit Wheel-/Paket-SHA256.
Der Container wurde entfernt; der Host erhielt keine APT-Installation. Die Testpaket-
Maintaineradresse ist ausdrücklich ein Platzhalter. Dieser Nachweis betrifft das
Plattformwheel und die Paketierungsmechanik; keine Fachanwendung wurde migriert und
keine noch unimplementierte Fachbibliothek wurde als fertig ausgegeben.

## Installierte Plattform: vollständiger Paketierungsweg per CLI

Die folgenden Befehle gehören zur installierten `auditcore`-Distribution; ein
Repositoryskript oder ein Consumer mit kopiertem Bibliotheksquellcode ist dafür
nicht erforderlich. Das Beispiel verwendet ausschließlich technische Testpakete.

```bash
# Auf dem Buildsystem: deklarierte Buildwerkzeuge vorher bereitstellen.
python -m pip install 'auditcore[deploy]'
auditcore-deploy build-python /path/to/technical-package \
  --output /srv/builds/test-release --source-date-epoch 1700000000

auditcore-deploy build-library /srv/builds/test-release/auditcore_fixture-1.0.0-py3-none-any.whl \
  --output /srv/builds/test-deb --source-date-epoch 1700000000 \
  --maintainer 'Packaging Test <packaging@example.invalid>'

auditcore-deploy pip-index \
  /srv/builds/test-release/auditcore_fixture-1.0.0-py3-none-any.whl \
  --output /srv/package-releases/test-index
```

`pip install auditcore[deploy]` setzt eine konfigurierte Quelle mit dem tatsächlich
bereitgestellten Plattformpaket voraus. Alternativ wird das verfügbare Plattformwheel
mit Extras aus dem eigenen freigegebenen Wheelhouse installiert. Es wird keine
öffentliche Verfügbarkeit des Namens behauptet.

`build-python` liest den konkreten `pyproject.toml`, arbeitet auf einem temporären
Quellsnapshot und ruft den installierten Buildbackend mit `--no-isolation` auf.
Backend und dessen deklarierte Abhängigkeiten müssen bereits vorhanden sein.
Es erfolgen keine automatischen Backenddownloads; `PIP_NO_INDEX=1` wird an den
Buildprozess weitergegeben. Ein Buildbackend führt Projektcode aus, deshalb wird
nur eine geprüfte, zur Ausführung freigegebene Paketquelle übergeben. Wheel und
sdist werden auf identischen Namen/Version und sichere Archivpfade geprüft. Der
Build liefert SHA256-Manifeste und eine CycloneDX-SBOM des Wheels. Ohne optionalen
Schema-Validator bleibt die SBOM-Schemaprüfung `NOT_EXECUTED`.

`pip-index` akzeptiert mehrere Wheels und Versionen. Das Ziel muss leer sein;
bestehende Releaseverzeichnisse werden nicht überschrieben. Das Ergebnis ist ein
lokaler [Python Simple API Index](https://packaging.python.org/en/latest/specifications/simple-repository-api/)
mit normalisierten Distributionsverzeichnissen, relativen Wheellinks und SHA256-
Fragmenten. Direkte URL-Abhängigkeiten und fremde Paketnamensräume werden abgelehnt.
Deklarierte Pflichtdependencies werden im Indexmanifest erfasst; deren vollständige
Auflösung beweist erst die Consumerinstallation. Optionale Extras sind gesondert
sichtbar und werden nicht still zu Pflichtpaketen.

Ein lokaler Consumer kann beispielsweise folgende **tatsächlich verfügbare**
Testpakete aus einem solchen Index laden:

```text
--index-url file:///srv/package-releases/test-index/simple/
auditcore_fixture==1.0.0
```

```bash
python3 -m venv /tmp/consumer-venv
/tmp/consumer-venv/bin/python -m pip install -r requirements.txt
```

Für produktive Freigaben enthält das Requirements-Lock zusätzlich die exakten
Hashes aller Abhängigkeiten und wird mit `--require-hashes` installiert. Ein
statischer interner Webserver kann denselben Index bereitstellen; diese Funktion
startet keinen Server und veröffentlicht keine Dateien extern. APT wird weiterhin
über `auditcore-deploy apt-repo build ... --signing-key ...` vorbereitet.

Die automatisierten Tests bauen zwei isolierte technische Pakete mit tatsächlicher
Abhängigkeit untereinander, erstellen den lokalen Index, installieren beide mit
Requirements und `--require-hashes` in einer neuen venv und führen isolierte
`python -I`-Imports sowie einen tatsächlichen Funktionswertvergleich aus.

## Wiederholbarer signierter APT-Lebenszyklustest

Nach Installation des frisch gebauten Plattformwheels in einer separaten venv:

```bash
python scripts/library_apt_selfcheck.py \
  --platform-python /path/to/installed-platform/bin/python \
  --platform-wheel dist/auditcore-0.1.0-py3-none-any.whl \
  --output .auditcore/framework-apt-proof
```

Ein frisches Ausgabeverzeichnis ist erforderlich. Das Skript ruft die neben diesem
Python installierte `auditcore-deploy`-CLI auf. Es erzeugt ausschließlich technische
Fixture-Wheels der Versionen 1 und 2 und verwendet das bestehende Debian-Testimage.
Falls dieses fehlt, bereitet `--prepare-image` es ausdrücklich auf dem Buildsystem vor.

Die beiden lokalen APT-Repositories werden mit einem eigens erzeugten temporären
Testschlüssel signiert. Im Wegwerfcontainer wird `signed-by` mit dessen öffentlichem
Keyring verwendet, niemals `trusted=yes`. Installation, tatsächlicher Systempython-
Funktionsaufruf, Upgrade, erneuter Funktionsaufruf und Remove laufen mit
`--network none`. Ein absichtlich nach dem Signieren veränderter Index muss von APT
abgelehnt werden. Optional wird auch das angegebene Plattformwheel als Debianpaket
installiert und über seine Imports und CLI-Hilfeaufrufe geprüft.

`result.json`, `commands.json`, `container-test.log` und Paketmanifeste binden die
Ergebnisse an die Artefakthashes. Der Umfang lautet ausdrücklich
`SYNTHETIC_TECHNICAL_FIXTURE`. Der Bericht unterscheidet eine editable Entwicklungs-
installation der ausführenden Plattform vom installierten Wheel. Temporäre private
Signierschlüssel und Container werden entfernt. Keine Hostinstallation, fachliche
Anwendungsmigration oder externe Veröffentlichung ist Teil dieses Nachweises.
