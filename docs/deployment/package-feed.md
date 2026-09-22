# Preview-Paketquelle vorbereiten und verwenden

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

Der geplante Downloadpfad ist
`https://github.com/janpow77/auditcore/releases/download/v0.1.0`.
Er ist erst nach einem gesonderten Release-Upload verfügbar. `PREVIEW_ASSETS_PREPARED`
beweist keine Veröffentlichung und keinen erfolgreichen Zugriff über diesen URL.
Nach dem Upload werden pip und APT in frischen isolierten Umgebungen gegen den
tatsächlichen öffentlichen Downloadpfad getestet, einschließlich GitHub-Redirects.
Der Release ist eine Bibliotheks-Preview, keine Freigabe einer Fachanwendung.

## pip aus einem eigenen Anwendungsrepository

Nach erfolgreicher Veröffentlichung kann die bereitgestellte Datei
`requirements-auditcore_invoicegenerator.txt` übernommen werden. Sie enthält
`--no-index`, SHA256-gebundene `--find-links`-URLs auf die einzelnen Wheels und
genau eine fachliche Anforderung:

```text
auditcore_invoicegenerator==0.1.0
```

```bash
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

Nach Veröffentlichung und erfolgreichem öffentlichen Installtest:

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
