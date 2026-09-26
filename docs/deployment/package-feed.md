# Öffentliche Preview-Paketquelle verwenden

**Aktuell: [Preview v0.4.2](https://github.com/janpow77/auditcore/releases/tag/v0.4.2)**
mit 27 Python-Distributionen und 9 npm-Paketen (185 Assets). Neu sind
`auditcore_extrapolation` 0.1.0 (Hochrechnung, TER und RER) und
`auditcore_common` 0.2.0 (Modul `rest`), dazu REST-Verträge in documents 0.4.0,
identifiers 0.2.0 und reporting 0.3.0. Alle übrigen Pakete tragen neue Pins
(`auditcore_common==0.2.0`). Erstmals liegen die npm-Pakete `@auditcore/*` als
signierte Tarballs bei.
Downloadpfad `https://github.com/janpow77/auditcore/releases/download/v0.4.2`;
derselbe Signaturschlüssel wie v0.1.0. Pro Paket gibt es `requirements-<paket>.txt`
(hashgebunden, `--no-index`), dazu `requirements-all-locked.txt` und die
Renderer-Locks für invoice (`pdf`) und reporting (`excel`). Am 26.09.2026 wurden
gegen den öffentlichen Pfad anonym geprüft: pip-Installation aller 27 Pakete
(hashgebunden und über den Paketindex) mit Funktionsprüfung, APT-Installation
samt Funktionsprüfung und Entfernung sowie die Installation aller 9 npm-Pakete
aus den Tarball-URLs. [Nachweis](../reports/domain-public-installation-v0.4.2.json),
[npm-Nachweis](../reports/npm-tarball-installation-v0.4.2.json).
Vorgänger v0.4.1: [Nachweis](../reports/domain-public-installation-v0.4.1.json),
v0.4.0: [Nachweis](../reports/domain-public-installation-v0.4.0.json),
v0.3.2: [Nachweis](../reports/domain-public-installation-v0.3.2.json).

Wheels in v0.4.2 (SHA-256):

| Distribution | Version | Wheel-SHA-256 |
|---|---|---|
| `auditcore_auth` | 0.1.1 | `0af1a2a8c27dd4d2847cfb4e90fe4a46c7f0dd2ca96fd5a1bd7e832b77c20f9b` |
| `auditcore_bpmn` | 0.1.2 | `8419ad7f93874999c7ad5038621b08efb36834dc953b88386d98ae60f4e50cba` |
| `auditcore_common` | 0.2.0 | `08971a3a3128c26e6230414ae338e22186e030a0ffe034758f267cae11539456` |
| `auditcore_dataprotection` | 0.5.1 | `9fd7a540b53ee28a44a1edc5093f434a64469697c71f83f9ba577c0bcf10e1da` |
| `auditcore_documents` | 0.4.0 | `d29319749e6c458140bbe153ccaa450eea16ce95c8191f733614db48f952dc2d` |
| `auditcore_dummygenerator` | 0.1.3 | `854afcdf7a14765ddca2acb33226099c223e464c244e6fc05969b3223b8fd457` |
| `auditcore_entity_matching` | 0.2.4 | `a289fdd1132538eb0984793c98260487bfb16795242763e4cba6462dcb90074e` |
| `auditcore_extrapolation` | 0.1.0 | `0ca9a6634ac9392fdb3731a35309e8e381cd21ead763f1b129fbdbb091df7900` |
| `auditcore_funding_sources` | 0.1.5 | `1b8cdbda142afbf2a1dd9a3bf02f304d7016b2afe9205c3355391a0534c145bc` |
| `auditcore_geo` | 0.3.1 | `7d674abef3675cc50326005a30f7341803207b7dae6d91b39c1d935745f75a70` |
| `auditcore_harvest` | 0.1.3 | `b5d08aa53e21f488277bd5df14b9d0df9aa4795b7f3fe6c3650ee0797600adb9` |
| `auditcore_identifiers` | 0.2.0 | `ee7e4df7a64ceb6b047c015bbc7ede2ae6e696cb59bd50f3c3e7ac880be28631` |
| `auditcore_invoicegenerator` | 0.2.3 | `e56c2af581677cf12c4485291e318f13d0d723ed93058ab178ce15ae09cb1f6a` |
| `auditcore_invoicesynth` | 0.2.0 | `e22380b0426655f14b5dc3c02246e4aef658b5ea4936a0a6b1113b2f3966433d` |
| `auditcore_kanban` | 0.1.2 | `569c89f84f4289c9608fef8a4ca821db32596a518881f1bc4feddfd3ea59432d` |
| `auditcore_legal_sources` | 0.1.5 | `f82611b739c226675e5507c67d74c52e58ef2820ee700375bd189b743aa08554` |
| `auditcore_llm_client` | 0.1.2 | `56be64b8d6b5c53bf2a2f3a763bbee8b48ad0e0274677fafca003df960928b1b` |
| `auditcore_market_indicators` | 0.1.3 | `0e359850489db6ed7e284260989527603ebc65f5b2987da6a75572155cd92895` |
| `auditcore_price_analysis` | 0.1.3 | `69423286e560b4d1ce25cb0ade227b803d526ee0db20d825eb19638bbc93b0e2` |
| `auditcore_price_sources` | 0.1.3 | `f48ee1f9dd1ab3dfc283b17e40a0cfc5e76152f496a36c75acb6264796211d74` |
| `auditcore_procurement` | 0.2.4 | `4b2271bf17bdd39955d56091b6cb77e8db275e56f1c8b1bbccd2769b117917e7` |
| `auditcore_property_sources` | 0.1.3 | `afee96064a67d0d786be548ae9d2c19789eaa4f6f9d5d53d335035c8c52dd1dc` |
| `auditcore_registry_sources` | 0.2.3 | `9fba74ab942874128794dcebb396e965cb50ade299b7740866e394f1a19acec6` |
| `auditcore_reporting` | 0.3.0 | `b0058d75d82e5367942ebed8e1381ac994cf8874ad30afee92f511672a8069a2` |
| `auditcore_risk` | 0.3.4 | `811970b803f1609e3e0810d18170428c97d15b9361f0e0cd3487b1c2916c5b69` |
| `auditcore_sampling` | 0.2.3 | `30391db774421c955a200e590efeb22766a1fb1b947dc009df2891d4bc3ae63c` |
| `auditcore_statistics` | 0.3.4 | `7ef4b80d8b006ac820f13baf80e40b3db1cf19600751ee922c9ba3ad5ad80d5a` |

npm-Tarballs in v0.4.2 (`npm-packages.json`; Integrität wie in `package-lock.json`):

| Paket | Version | Datei | SHA-256 | npm-Integrität |
|---|---|---|---|---|
| `@auditcore/bpmn-editor` | 0.1.1 | `auditcore-bpmn-editor-0.1.1.tgz` | `fc0a57099cd162b05ebdfa2fb4cd5a5659175ec4408ee8a7aa1bf7c10f18287f` | `sha512-iuttfny2f7iWGLdtQTv0IzkaCAq+JZC3iB32jkz5OmgAemzLIF0D6lZ/P/wpX4QJ/V68M4O9oHT6d+/oRmIjig==` |
| `@auditcore/bpmn-flowaudit` | 0.2.1 | `auditcore-bpmn-flowaudit-0.2.1.tgz` | `96b218831c4a7dbdf8b402f98102f4f4d604e64d71b32487029e14f7316657ab` | `sha512-TQKFoL56gpzk3hlWb6ttH7s4ZHRwNeks+8WiPHK5JBmQMhtFmL3AUwnB6a5gwadHXEMfBIQLFq5aNaqhkOU26g==` |
| `@auditcore/bpmn-react` | 0.2.1 | `auditcore-bpmn-react-0.2.1.tgz` | `b4f7dc347c9f57733ce4dbbc74a1fb9915511b1fc64e364fd34e00bfb1d06dff` | `sha512-AQ0K1PN+LIAbrXHmnv+/zhFHrZJX7aO0qEkAML1PS7I5r8kNjErAzx2YdmG69X3gAG+U0nnrkgPyQETi9VgDHQ==` |
| `@auditcore/bpmn-vue` | 0.2.1 | `auditcore-bpmn-vue-0.2.1.tgz` | `0df240e60456519d7aa210496c301a6c390637f242ae43288847438f020a13fc` | `sha512-89j+W+h9/uz0yeNJAySgHPPZW2g6Zd0yNBIftRFVqUvsxriwZKMvDaE5kyxMLq4O9dndT1SpcDg84EWQI+PdFA==` |
| `@auditcore/common` | 0.1.1 | `auditcore-common-0.1.1.tgz` | `2d633cf1795faba04f6b385d829751f2999de0f6ad607d722daa812a7871a514` | `sha512-Y+ss0woO3jOB7y91EaU3VmR4oxUDCUDv5h70OwE11PMESD7zG2BzcDb+1zDpnLhrCJZ4mG2qTV7eiZjdRoKpDw==` |
| `@auditcore/kanban-core` | 0.2.1 | `auditcore-kanban-core-0.2.1.tgz` | `fe084d2b267a1953c6227163bc977bbf5185812bde18768c6de4c0ba53d623a2` | `sha512-c9JNSqTAgmLZTDz9OGn4rGziBKHjw7MEOZwQKQJ8qFdIz16W7jC3eRPPzWgeVm085rjALzO9zALC9YXXn+tsxA==` |
| `@auditcore/ui` | 0.3.0 | `auditcore-ui-0.3.0.tgz` | `7c9e40bbfe14340aa99e5a98ed078743cfcfdbb9a3381ad9067ead5b7dd17760` | `sha512-C8JbW7soA9gm7JyXCKo84oFZ0Y8nihfSWb8HLpXybpoE+YONfJsNo11CJ7WkD3mMAH5X4SCZbNh08IVag4fYrg==` |
| `@auditcore/ui-core` | 0.2.0 | `auditcore-ui-core-0.2.0.tgz` | `fba4fc3a10c405044cc471ee48e3add88e19390af7a00a127f83087f4696b24d` | `sha512-iCFk974FY15VTr6Oa1z8Pxgzs9xMcjGKPKLEkXcOQTm29yO+hQuBFCbA5EsboyelUO2jhcOEXFwexdmhwTJ92w==` |
| `@auditcore/ui-react` | 1.1.0 | `auditcore-ui-react-1.1.0.tgz` | `2dc8ea65edb007bd98e25532f160f127e3e005803b69d8582baa5d7182f298a4` | `sha512-aFjq4J/iCr3yzRZ4RU4GXDHU3O2oZKL+BIriR5CIwwxrtGMX7GsvTDuBzfTVvE2zCiV6226wb/ZsTVOZICKwaA==` |

**npm-Pakete (`@auditcore/*`):** Seit v0.4.2 legt
`scripts/prepare_library_release.py` jedes Paket unter `packages-js/` als
`npm pack`-Tarball bei, mit `npm-packages.json` (npm-Integrität `sha512-…`,
SHA-256, vollständige Abhängigkeitshülle) und in `SHA256SUMS` samt Signatur
`SHA256SUMS.asc`. Der Workflow `npm-publish` veröffentlicht nach dem Release
genau diese Tarballs auf npmjs.org (Standardweg `npm install @auditcore/<paket>`,
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
