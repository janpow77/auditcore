# Öffentliche Preview-Paketquelle verwenden

**Aktuell: [Preview v0.3.1](https://github.com/janpow77/auditcore/releases/tag/v0.3.1)**
mit neunzehn Distributionen (126 Assets, Tag auf `a8b9b74`), darunter neu
auditcore_procurement 0.2.0, auditcore_risk 0.2.0 und auditcore_geo 0.2.0.
Downloadpfad `https://github.com/janpow77/auditcore/releases/download/v0.3.1`;
derselbe Signaturschlüssel wie v0.1.0. Pro Paket gibt es `requirements-<paket>.txt`
(hashgebunden, `--no-index`), dazu `requirements-all-locked.txt` und die
Renderer-Locks für invoice (`pdf`) und reporting (`excel`). Anonyme pip- und
APT-Installation aller neunzehn Pakete samt Funktionsprüfung und Entfernung wurde am
23.09.2026 gegen den öffentlichen Pfad ausgeführt:
[Nachweis](../reports/domain-public-installation-v0.3.1.json). Vorgänger v0.3.0:
[Nachweis](../reports/domain-public-installation-v0.3.0.json).

Zusätzlich gibt es einen Paketindex nach PEP 503 auf GitHub Pages, der die
Release-Dateien aller Versionen mit SHA-256 verlinkt:

```bash
pip install auditcore-geo --index-url https://janpow77.github.io/auditcore/simple/
```

Mit `--index-url` (nicht `--extra-index-url`) besteht kein Risiko, dass ein
gleichnamiges fremdes Paket von PyPI bezogen wird. Die folgenden Abschnitte
beschreiben das Verfahren am Beispiel v0.1.0; für v0.3.0 gelten sie mit dem
neuen Pfad und den Paketnamen des Releases. Vorgänger:
[v0.2.0](https://github.com/janpow77/auditcore/releases/tag/v0.2.0)
([Nachweis](../reports/domain-public-installation-v0.2.0.json)).

Die drei Fachbibliotheken sind eigenständig installierbare Distributionen im
Repository `auditcore`. Anwendungen behalten ihre eigenen Repositories und
deklarieren die benötigte Bibliothek in ihren Requirements oder Debian-Depends.
`auditcore_invoicegenerator` benötigt `auditcore_dummygenerator` transitiv.
Die Plattformwerkzeuge sind keine Laufzeitpflicht dieser Fachbibliotheken.

## Vorbereitung durch Maintainer

Die Vorbereitung veröffentlicht nichts. Sie erfordert einen vollständigen
erfolgreichen Lauf von `scripts/verify_domain_packages.py --apt` einschließlich
selektiver pip-Installation, tatsächlicher Importtests sowie APT-Installation,
Upgrade und Remove. Alte Testbauten mit ungeklärter Lizenz werden abgewiesen.

```bash
python scripts/prepare_library_release.py .auditcore/domain-packages-release \
  --platform-python .auditcore/domain-platform-venv/bin/python \
  --output .auditcore/release-assets-v0.1.0 --version 0.1.0
```

Das Skript verifiziert Nachweis- und Artefakthashes, MIT-Metadaten und den
konkreten Freigabenachweis der beiden übernommenen Generatorquellen. Es kopiert
ausschließlich die explizit geprüften Wheels, SDists und Debian-Revision 1,
die mit den Wheel-Hashes verbundenen validierten SBOMs sowie kleine öffentliche
Debian-Manifeste mit Version, Abhängigkeiten, Lizenz und Hashes ohne lokale Hostpfade,
erzeugt signierte Flat-APT-Indizes, Requirements und `SHA256SUMS`. Der öffentliche
Signaturschlüssel ist `auditcore-preview-keyring.gpg`; sein Fingerprint steht in
`preview-manifest.json`. Revision 2 dient ausschließlich dem lokalen Upgrade-Test.

Ein dedizierter persistenter Schlüssel entsteht bei Bedarf ausschließlich unter
`.auditcore/release-signing` (Verzeichnisse 0700, reguläre Dateien 0600). Dieser
bereits ignorierte Pfad wird niemals kopiert; bestehende persönliche GPG-Keys
werden nicht verwendet. Der lokale Schlüssel ist ohne interaktive Passphrase
für automatisiertes Signieren angelegt: Zugriffsschutz und gesicherte lokale
Aufbewahrung dieses Verzeichnisses gehören zum Maintainerbetrieb. Nur der
exportierte öffentliche Key gehört zu den Release-Assets. Kein Upload ganzer
`.auditcore`-Verzeichnisse oder Verifikationsprotokolle.

Die [Preview v0.1.0](https://github.com/janpow77/auditcore/releases/tag/v0.1.0)
ist mit 27 Assets veröffentlicht. Der Downloadpfad lautet
`https://github.com/janpow77/auditcore/releases/download/v0.1.0`.
Am 22.09.2026 wurden anonyme pip- und APT-Installationen, echte Funktionsaufrufe
und Entfernung gegen diesen öffentlichen URL erfolgreich ausgeführt,
einschließlich GitHub-Redirects. [Prüfnachweis](../reports/domain-public-installation.json).
Der beigefügte `preview-manifest.json` dokumentiert unverändert den Stand vor Upload;
er ist von diesem tatsächlichen Veröffentlichungsnachweis zu unterscheiden.
Der Release ist eine Bibliotheks-Preview, keine Freigabe einer Fachanwendung.

## pip aus einem eigenen Anwendungsrepository

Die bereitgestellte
[requirements-auditcore_invoicegenerator.txt](https://github.com/janpow77/auditcore/releases/download/v0.1.0/requirements-auditcore_invoicegenerator.txt)
kann in das Anwendungsrepository übernommen werden. Sie enthält
`--no-index`, SHA256-gebundene `--find-links`-URLs auf die einzelnen Wheels und
genau eine fachliche Anforderung:

```text
auditcore_invoicegenerator==0.1.0
```

```bash
curl -fsSLO https://github.com/janpow77/auditcore/releases/download/v0.1.0/requirements-auditcore_invoicegenerator.txt
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-auditcore_invoicegenerator.txt
.venv/bin/python -I -c 'from auditcore_invoicegenerator import InvoiceScenario'
```

Die deklarierte Dummy-Abhängigkeit wird dabei automatisch geladen. Es wird kein
Quellcode in das Anwendungsrepository kopiert. Für alle drei Bibliotheken mit
expliziten Hash-Locks gibt es `requirements-all-locked.txt`; für Dummy und
Reporting jeweils eine eigene selektive Requirements-Datei. Zusätzliche
Anwendungsabhängigkeiten benötigen ihren eigenen Index-/Lockvertrag, da diese
Dateien absichtlich nur die Preview-Wheels anbieten. Eine öffentliche
PyPI-Veröffentlichung wird hier nicht behauptet.

## APT auf Debian mit Python 3.11 oder neuer

Signaturschlüssel-Fingerprint: **`E427F95CC37CBFD0876314CA0D1580A6CAE37327`**.
Die folgenden Schritte wurden gegen die öffentliche Paketquelle geprüft:

```bash
BASE=https://github.com/janpow77/auditcore/releases/download/v0.1.0
curl -fsSL "$BASE/auditcore-preview-keyring.gpg" -o auditcore-preview-keyring.gpg
gpg --show-keys --with-fingerprint auditcore-preview-keyring.gpg
# Fingerprint gegen den separat geprüften Release-Nachweis abgleichen.
sudo install -m 0644 auditcore-preview-keyring.gpg /usr/share/keyrings/auditcore-preview.gpg
echo "deb [signed-by=/usr/share/keyrings/auditcore-preview.gpg] $BASE ./" \
  | sudo tee /etc/apt/sources.list.d/auditcore-preview.list
sudo apt-get update
sudo apt-get install python3-auditcore-invoicegenerator=0.1.0-1
/usr/bin/python3 -I -c 'from auditcore_invoicegenerator import InvoiceScenario'
```

APT installiert die passende Dummy-Abhängigkeit. `Signed-By` begrenzt das
Vertrauen auf diese Paketquelle; `trusted=yes` wird nicht verwendet. Pakete liegen
unter `/usr/lib/python3/dist-packages`; eine gewöhnliche isolierte venv sieht sie
nicht automatisch. Anwendungen wählen entweder pip in ihrer eigenen venv oder
Debian-Systempython mit passenden Paketabhängigkeiten. Auf dem Zielsystem sind
keine Compiler, Poetry, uv, npm, Node-Buildwerkzeuge oder PyPI-Downloads erforderlich.

Jede veröffentlichte Preview-Version behält ihre Artefakte unverändert. Ein Update
erhält einen neuen Releasepfad, neue Prüfnachweise und eine explizit ausgewählte
Version. Diese Flat-APT-Quelle behauptet keinen bereits betriebenen rollenden
Produktionskanal, Backupdienst oder Anwendungsschutz.
