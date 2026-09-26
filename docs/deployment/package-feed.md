# Öffentliche Preview-Paketquelle verwenden

**Aktuell: [Preview v0.4.1](https://github.com/janpow77/auditcore/releases/tag/v0.4.1)**
mit 26 Distributionen (168 Assets). Sicherheitskorrektur in auditcore_harvest
0.1.2 (Feeds nur über defusedxml, Extra `xml`), Zahleneingabe nach dem Vertrag
`parse-number` (auditcore_common 0.1.1, price_analysis 0.1.2,
property_sources 0.1.2), REST-Module für VVT/DSFA (dataprotection 0.5.0) und
Geo-Karte (geo 0.3.0); alle übrigen geänderten Pakete mit neuen Pins
(`auditcore_common==0.1.1`, `auditcore_harvest==0.1.2`). auth, identifiers und
llm_client sind byte-gleich zu v0.4.0. Die signierte APT-Release-Datei trägt
jetzt ein `Date`-Feld.
Downloadpfad `https://github.com/janpow77/auditcore/releases/download/v0.4.1`;
derselbe Signaturschlüssel wie v0.1.0. Pro Paket gibt es `requirements-<paket>.txt`
(hashgebunden, `--no-index`), dazu `requirements-all-locked.txt` und die
Renderer-Locks für invoice (`pdf`) und reporting (`excel`). Anonyme pip-Installation
(hashgebunden und über den Paketindex) und APT-Installation aller 26 Pakete samt
Funktionsprüfung und Entfernung wurde am 26.09.2026 gegen den öffentlichen Pfad
ausgeführt: [Nachweis](../reports/domain-public-installation-v0.4.1.json).
Vorgänger v0.4.0: [Nachweis](../reports/domain-public-installation-v0.4.0.json),
v0.3.2: [Nachweis](../reports/domain-public-installation-v0.3.2.json).

Wheels in v0.4.1 (SHA-256):

| Distribution | Version | Wheel-SHA-256 |
|---|---|---|
| `auditcore_auth` | 0.1.0 | `e5fa62b78c06d51527ba3fe208a52fd0c0345c38076fb673f63a40ded769f4e6` |
| `auditcore_bpmn` | 0.1.1 | `3707df29a78341a5c16e469364203d86d0b430635a0ff0804ada7b17658cd72f` |
| `auditcore_common` | 0.1.1 | `5b6c5659de0d1bb7b8d2c175e295851a5be64a56223050d27c75645b13b90ebd` |
| `auditcore_dataprotection` | 0.5.0 | `8120e2f5a54edd57b0277acb18cbe5dd2be5477d6cbfbfc15c8df1ad91a5b407` |
| `auditcore_documents` | 0.3.3 | `7ad288d593c9ea5f6578d38c9ed94660186c23729ea31bf52e8817ec153305f4` |
| `auditcore_dummygenerator` | 0.1.2 | `cd90f739551af590f560a167f2e2a70f71aed79f8972500e672265d97ad3bf90` |
| `auditcore_entity_matching` | 0.2.3 | `8865ffc99778f76770f1550b5ea2fc57a47af24d47d2fdc9ed4a9e283ebc7e43` |
| `auditcore_funding_sources` | 0.1.4 | `30eef49841af00ed791855d40d608d7122fc9cf0a471c428f546b300b0ece919` |
| `auditcore_geo` | 0.3.0 | `90b4ee3cbe14347706bbdf522e17c6a92425050dd680aedbcabf96a8733936b5` |
| `auditcore_harvest` | 0.1.2 | `4e2a7845fce2ff34d25a77c6cfbd629a342a7cbeec510d06ca2be03719cf0746` |
| `auditcore_identifiers` | 0.1.0 | `fb4f0217fd80f7290f799dc1ac12e0717eb770a99d34644082e0b71e084693bb` |
| `auditcore_invoicegenerator` | 0.2.2 | `540994598e88ff77e01966823264e196b71a2fe34800a2010af45befdf1715f9` |
| `auditcore_invoicesynth` | 0.1.2 | `92b6b0cc464f38a1186254d3606349aea5781d99ada76540931448b355c1ef01` |
| `auditcore_kanban` | 0.1.1 | `ede5980d5c1b13509b17059f94c832ff02a35d60ee94ae2e05e6229b207c12a7` |
| `auditcore_legal_sources` | 0.1.4 | `7e42231daf1dccda2a01a5fcd00606c69500d0e31ef13eb58930f9e4d44f5ba6` |
| `auditcore_llm_client` | 0.1.1 | `2de349bda575a23398f6273f748769676fb9e58114911b0da2a9c75edaeda552` |
| `auditcore_market_indicators` | 0.1.2 | `f1c738da3048cdbbc0bcd2c0ddc483e6adffc3e825c2b2a98ea7581e9a3d7666` |
| `auditcore_price_analysis` | 0.1.2 | `43e225c80c6be00b3c1a511bccbbe6a7d41f188048f18748885c375bb5290100` |
| `auditcore_price_sources` | 0.1.2 | `be2f1d7eca48d73752fa7e42b5d4b37c637b79861c9467dbc6aa102604a98c3a` |
| `auditcore_procurement` | 0.2.3 | `aaee40807b3284f6f4f3302e4f19ee8ceafabba221ffd1b6dd07138b6e97c12e` |
| `auditcore_property_sources` | 0.1.2 | `91059653c498aaa9c7bd14d57ad6bcb6b47f11d122320c17ec5d895515c811cb` |
| `auditcore_registry_sources` | 0.2.2 | `177ee3bb37ad533df9de70427bbd9ad343c604589fa000826a2cdd3665e8197d` |
| `auditcore_reporting` | 0.2.2 | `417f78ca06b8458860699a88728e15118a855a41d8999fc58b87aadab9ce4ba8` |
| `auditcore_risk` | 0.3.3 | `2c652183426f139c053063d4334f4bc9f8667e5f7f36f171c60d547b03e83b60` |
| `auditcore_sampling` | 0.2.2 | `c735af5fea79f0b47506f789c0df8b6e21d5391a41e537659cc68d48b9d0a6b1` |
| `auditcore_statistics` | 0.3.3 | `cdc9a14dc2ec778c26f6dc71e16c7fc615aeaff8305f0934904f915f3fafc177` |

**npm-Pakete (`@flowaudit/*`):** v0.4.1 und ältere Releases enthalten sie nur
im Quellstand des Tags, nicht als Release-Dateien. Ab dem nächsten Release legt
`scripts/prepare_library_release.py` jedes Paket unter `packages-js/` als
`npm pack`-Tarball bei, mit `npm-packages.json` (npm-Integrität `sha512-…`,
SHA-256, vollständige Abhängigkeitshülle) und in `SHA256SUMS` samt Signatur
`SHA256SUMS.asc`. Der Workflow `npm-publish` veröffentlicht nach dem Release
genau diese Tarballs auf npmjs.org (Standardweg `npm install @flowaudit/<paket>`,
Einrichtung in [npm-veroeffentlichung.md](npm-veroeffentlichung.md)); die
Tarball-URLs bleiben der Weg für Intranet und Offline-Betrieb.
Installation in Vue-, React- und framework-freien Anwendungen:
[frontend-installation.md](frontend-installation.md).

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
erzeugt signierte Flat-APT-Indizes, Requirements und `SHA256SUMS` mit
abgetrennter Signatur `SHA256SUMS.asc`. Zusätzlich baut es aus dem committeten
Stand von `packages-js/` jedes npm-Paket (`npm run build`, `npm pack`) und
beschreibt die Tarballs in `npm-packages.json` (siehe
[frontend-installation.md](frontend-installation.md)). Der öffentliche
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
