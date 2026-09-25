# Öffentliche Preview-Paketquelle verwenden

**Aktuell: [Preview v0.4.0](https://github.com/janpow77/auditcore/releases/tag/v0.4.0)**
mit 26 Distributionen (168 Assets), darunter neu auditcore_common 0.1.0,
auditcore_auth 0.1.0, auditcore_identifiers 0.1.0, auditcore_llm_client 0.1.1,
auditcore_kanban 0.1.0 und auditcore_bpmn 0.1.0; alle übrigen Pakete in neuer
Version (Refaktorierungen ohne Verhaltensänderung, Hilfsfunktionen aus
auditcore_common, einheitlicher Pin `auditcore_harvest==0.1.1`).
Downloadpfad `https://github.com/janpow77/auditcore/releases/download/v0.4.0`;
derselbe Signaturschlüssel wie v0.1.0. Pro Paket gibt es `requirements-<paket>.txt`
(hashgebunden, `--no-index`), dazu `requirements-all-locked.txt` und die
Renderer-Locks für invoice (`pdf`) und reporting (`excel`). Anonyme pip-Installation
(hashgebunden und über den Paketindex) und APT-Installation aller 26 Pakete samt
Funktionsprüfung und Entfernung wurde am 25.09.2026 gegen den öffentlichen Pfad
ausgeführt: [Nachweis](../reports/domain-public-installation-v0.4.0.json).
Vorgänger v0.3.2: [Nachweis](../reports/domain-public-installation-v0.3.2.json),
v0.3.1: [Nachweis](../reports/domain-public-installation-v0.3.1.json).

Wheels in v0.4.0 (SHA-256):

| Distribution | Version | Wheel-SHA-256 |
|---|---|---|
| `auditcore_auth` | 0.1.0 | `e5fa62b78c06d51527ba3fe208a52fd0c0345c38076fb673f63a40ded769f4e6` |
| `auditcore_bpmn` | 0.1.0 | `fadc1f137ab4183cb27ae26a664f521d03f8baf5226031e0f809e2f8419746ad` |
| `auditcore_common` | 0.1.0 | `e8b83c282d5306a075f0f051e3f74865b619002272671e90cfc586918ef21eeb` |
| `auditcore_dataprotection` | 0.4.3 | `25f5478b1007ddbfadbc0212136032af3650db0a92f77ca5f7a0d3b8136da18a` |
| `auditcore_documents` | 0.3.2 | `fb306c651e5871a1dba8b1a2e4a14f7f8222b650feb02921fe968ccab766d1e9` |
| `auditcore_dummygenerator` | 0.1.1 | `eaf1f9ff55f5b6044d697f43ed51aeb7ddaf9180763acb9c1dbd0ca238826864` |
| `auditcore_entity_matching` | 0.2.2 | `efc579d8d7753fd311bb4124be043d3f1dd301644809a432434c259c72e2167a` |
| `auditcore_funding_sources` | 0.1.3 | `8ec5ace1f23a0e5dc29d8b473825296d271af71117e0caf46235f530eafe3f77` |
| `auditcore_geo` | 0.2.1 | `3433bd595e51d8d08b8c7ba98fdf667f7158cd0c07fe822af7ed92ab39acf963` |
| `auditcore_harvest` | 0.1.1 | `35f3deff4f5b8e9d741fbc93f67050056ab10669003c929f0ae2c07421731b87` |
| `auditcore_identifiers` | 0.1.0 | `fb4f0217fd80f7290f799dc1ac12e0717eb770a99d34644082e0b71e084693bb` |
| `auditcore_invoicegenerator` | 0.2.1 | `7546b5c7f210eb40a77a6cb92054c5ee643842758592ff5422bdff8069c9da33` |
| `auditcore_invoicesynth` | 0.1.1 | `3d91e3d97e8bca8de7f909b731cbac72d989be835267805cabef81732a70709b` |
| `auditcore_kanban` | 0.1.0 | `260c50cf6a37c570955886d8455c41650c9329ed53a20b2ddaec5254365afb76` |
| `auditcore_legal_sources` | 0.1.3 | `87419f5ddc0a4b93b3865f1db851ccf6680043ea5b54674a4f380c4a6b861e0d` |
| `auditcore_llm_client` | 0.1.1 | `2de349bda575a23398f6273f748769676fb9e58114911b0da2a9c75edaeda552` |
| `auditcore_market_indicators` | 0.1.1 | `c92a5aba7a5c4692b903fe773dcdd6f3fc51293694e9bc62544a90a93cb54371` |
| `auditcore_price_analysis` | 0.1.1 | `b428839afd4dae267a902f7c73ef7a83f0340a7d9f886b1803de44f36523cc8f` |
| `auditcore_price_sources` | 0.1.1 | `a21eba39ad14f7a847b256bf44a12345e859b8e09df910e9be64cedb32edc5c7` |
| `auditcore_procurement` | 0.2.2 | `dfc0500d0392f5d030c626a193d7556ae176e9687565f69d1e4bcfacc0a7478b` |
| `auditcore_property_sources` | 0.1.1 | `76f5877d8f5efba1cb8ff49ef9ef712d75e0c7e8d2634622c80542e682c202aa` |
| `auditcore_registry_sources` | 0.2.1 | `dd958343bf84ad6c58be68a1f1f41823ec047d4bf986ad64d74b176b97b2ec89` |
| `auditcore_reporting` | 0.2.1 | `d9d982be1b21bacc4bd6596b1dc95208987ece5cdfb278c61fa2a6fc48a24ad7` |
| `auditcore_risk` | 0.3.2 | `72f596b5fc0a66a8b4c80a1f1addf1f24601ac19a9e35c31dd2426dd783c8047` |
| `auditcore_sampling` | 0.2.1 | `c71cb6d341997c1db74736f68ed0edb980f8ef4efa691c97180fb0b376c2bc2e` |
| `auditcore_statistics` | 0.3.2 | `24afa69d1628bad9b110db2e5bd8c9cd8f71a4862d9666286da8e42a75563753` |

Die npm-Pakete unter `packages-js/` (`@flowaudit/*` 0.1.0) sind im Quellstand des
Tags enthalten, werden mit diesem Release aber nicht auf npm veröffentlicht.

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
