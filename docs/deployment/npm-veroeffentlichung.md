# npm-Veröffentlichung der `@auditcore`-Pakete einrichten

Die Frontend-Pakete unter `packages-js/` erscheinen nach jedem GitHub-Release
auf [npmjs.org](https://www.npmjs.com/org/auditcore). Veröffentlicht werden
genau die signierten Tarballs des Releases; neu gebaut wird nichts. Diese
Anleitung beschreibt die einmalige Einrichtung und den Ablauf je Release.
Anwendungen installieren danach mit `npm install @auditcore/<paket>`
([frontend-installation.md](frontend-installation.md)).

## Was der Workflow tut

`.github/workflows/npm-publish.yml` läuft bei `release: published` und von
Hand (`workflow_dispatch` mit Release-Tag, standardmäßig nur als Probelauf).

1. **Prüfen** (Job `verify`, ohne Schreibrechte): lädt `npm-packages.json`,
   alle `auditcore-*.tgz`, `SHA256SUMS`, `SHA256SUMS.asc` und den
   Schlüsselbund des Releases; prüft den Fingerprint
   `E427F95CC37CBFD0876314CA0D1580A6CAE37327`, die Signatur und die SHA-256
   der Dateien. `scripts/npm_publish.py` bindet dann jeden Tarball an seinen
   Eintrag in `npm-packages.json` (SHA-256, Größe, npm-Integrität, Name,
   Version, MIT, `repository` = `janpow77/auditcore`) und erstellt den Plan.
   Releases ohne `npm-packages.json` (v0.4.1 und älter) werden übersprungen.
2. **Veröffentlichen** (Job `publish`, Umgebung `npm`, `id-token: write`):
   prüft dieselben Dateien erneut und ruft je Paket
   `npm publish <tarball> --provenance --access public --tag <tag>` auf, in
   Abhängigkeitsreihenfolge (`bpmn-editor`, `bpmn-flowaudit`, `common`,
   `kanban-core`, dann `ui-core`, dann `bpmn-react`, `bpmn-vue`, `ui`,
   `ui-react`).
   - Version schon auf npm mit gleicher Integrität: übersprungen. Ein
     abgebrochener Lauf lässt sich daher einfach wiederholen.
   - Version schon auf npm mit anderem Inhalt (z. B. unveränderte Version,
     aber mit neueren Werkzeugen gebaut): nie überschrieben. Die übrigen Pakete
     werden veröffentlicht, der Lauf endet rot; der Plan warnt vorher. Dann
     fehlt eine Versionsanhebung im Paket.
   - dist-tag: `next` für Vorabversionen (`x.y.z-rc.1` usw.), sonst `latest`.
     Ist auf npm schon eine höhere Version `latest`, erhält eine ältere den
     Tag `previous`, damit `latest` nicht zurückspringt. Maßgeblich ist die
     Paketversion, nicht der Vorab-Haken des GitHub-Releases (den tragen alle
     bisherigen auditcore-Releases).

Anmeldung bei npm: bevorzugt **Trusted Publishing** (OIDC, kein
gespeichertes Geheimnis). npm vertraut dann nur dem Workflow `npm-publish.yml`
in `janpow77/auditcore`. Das Secret `NPM_TOKEN` ist nur für die
Erstveröffentlichung vorgesehen (siehe Schritt 4), weil npm einen Trusted
Publisher erst für ein vorhandenes Paket annimmt.

## Einmalige Einrichtung

### 1. npm-Konto und Zwei-Faktor-Anmeldung

1. Auf <https://www.npmjs.com/signup> ein Konto anlegen (oder das vorhandene
   nutzen) und die E-Mail-Adresse bestätigen.
2. *Avatar → Account → Two-Factor Authentication*: 2FA einschalten, Modus
   **„Authorization and writes“**. Sicherheitsschlüssel oder
   Authenticator-App; die Wiederherstellungscodes sicher ablegen.

### 2. Organisation `@auditcore` anlegen

1. *Avatar → Add Organization*, Name **`auditcore`**, Plan **Free**
   (unbegrenzt viele öffentliche Pakete).
2. Stand 26.09.2026 ist der Scope frei: `npm view @auditcore/ui` liefert 404,
   die Registry meldet für `auditcore` „Scope not found“. Den Namen bald
   sichern; wer ihn zuerst belegt, besitzt alle `@auditcore/*`-Namen.
3. *Organization → Settings*: „Require two-factor authentication“ für alle
   Mitglieder einschalten.

### 3. GitHub vorbereiten

Im Repository `janpow77/auditcore` unter *Settings*:

1. *Environments → New environment* **`npm`**. Empfohlen: *Required
   reviewers* (eigenes Konto) und *Deployment branches and tags* auf Tags
   `v*` beschränken. Dann wartet jede Veröffentlichung auf eine Freigabe.
2. Für die Erstveröffentlichung: *Environments → npm → Environment secrets*
   **`NPM_TOKEN`** (Schritt 4).
3. Automatik nach dem Release: *Secrets and variables → Actions → Variables*
   **`NPM_PUBLISH_ENABLED`** = `true`. Ohne diese Variable läuft der Workflow
   nur von Hand. Sie verhindert, dass ein Release vor der Einrichtung einen
   roten Lauf erzeugt.

### 4. Erstveröffentlichung mit Token

Voraussetzung: ein Release mit npm-Tarballs (der erste nach v0.4.1).

1. npm: *Avatar → Access Tokens → Generate New Token → Granular Access
   Token*. Name `auditcore-erstveroeffentlichung`, Ablauf **7 Tage**,
   *Bypass two-factor authentication* anhaken (sonst verlangt `npm publish`
   im Workflow ein Einmalpasswort), *Packages and scopes*: **Read and write**,
   Auswahl *Organization* `auditcore` bzw. alle Pakete des Scopes.
2. Token als Environment-Secret `NPM_TOKEN` der Umgebung `npm` speichern
   (Schritt 3.2) und lokal nirgends ablegen.
3. *Actions → npm-publish → Run workflow*: `tag` = `v0.4.2` (Beispiel),
   `dry_run` angehakt lassen. Im Job `verify` stehen im Protokoll und im
   Artefakt `npm-release-assets/npm-publish-plan.json` alle neun Pakete mit
   `"action": "publish"`.
4. Dasselbe mit `dry_run` **aus**. Nach der Freigabe der Umgebung
   veröffentlicht der Job `publish`; die Zusammenfassung des Laufs listet
   Paket, Version, Aktion und dist-tag.
5. Prüfen: `npm view @auditcore/ui` zeigt Version und `dist.integrity` (gleich
   `integrity` in `npm-packages.json`); auf npmjs.com trägt jedes Paket das
   Provenance-Abzeichen mit Verweis auf Workflow und Commit.

### 5. Auf Trusted Publishing umstellen

Für **jedes** der neun Pakete (`common`, `kanban-core`, `ui-core`, `ui`,
`ui-react`, `bpmn-editor`, `bpmn-flowaudit`, `bpmn-vue`, `bpmn-react`) auf
npmjs.com *Paket → Settings → Trusted Publisher → GitHub Actions*:

| Feld | Wert |
|---|---|
| Organization or user | `janpow77` |
| Repository | `auditcore` |
| Workflow filename | `npm-publish.yml` |
| Environment name | `npm` |

Danach auf derselben Seite unter *Publishing access* **„Require two-factor
authentication and disallow tokens“** wählen. Dann das Token in npm
widerrufen und das Secret `NPM_TOKEN` in GitHub löschen. Der Workflow meldet
sich ab jetzt per OIDC an (npm ≥ 11.5.1, im Workflow fest auf 11.16.0).

Kommt später ein **neues Paket** unter `packages-js/` hinzu, braucht es für
seine erste Version wieder den Weg aus Schritt 4 (kurzlebiges Token) und
danach seinen eigenen Trusted Publisher.

## Ablauf je Release

1. Release wie bisher vorbereiten und veröffentlichen
   (`scripts/prepare_library_release.py`, Upload aller Dateien, dann
   *Publish release*). Die Dateien müssen **vor** dem Veröffentlichen des
   Releases hochgeladen sein; der Workflow startet beim Ereignis
   `release: published`.
2. Mit `NPM_PUBLISH_ENABLED=true` läuft `npm-publish` automatisch und wartet
   gegebenenfalls auf die Freigabe der Umgebung `npm`.
3. Unveränderte Pakete (gleiche Version, gleiche Integrität) werden
   übersprungen. Ein Paket mit geändertem Inhalt, aber alter Version, bleibt
   auf npm im alten Stand und färbt den Lauf rot: Version anheben und neuen
   Release erstellen.
4. Fehlgeschlagen oder ohne Automatik: *Run workflow* mit dem Tag, erst als
   Probelauf, dann mit `dry_run` aus.

## Fehlerbilder

| Meldung | Ursache und Abhilfe |
|---|---|
| `E404 Not Found - PUT https://registry.npmjs.org/@auditcore%2f…` | Organisation fehlt oder Konto ohne Schreibrecht; bei Trusted Publishing: Publisher für dieses Paket nicht eingerichtet oder Feld falsch (Workflow-Dateiname, Umgebung) |
| `E422 … provenance … repository.url` | `package.json#repository` im Tarball passt nicht zu `janpow77/auditcore`; wird schon in `verify` geprüft |
| `EOTP` | Token ohne *Bypass two-factor authentication* |
| `Version exists on npm with different content` | Version schon mit anderem Inhalt veröffentlicht; npm erlaubt kein Überschreiben, Version anheben |
| `SHA-256 does not match …` | Release-Datei nachträglich ersetzt oder unvollständig hochgeladen; Release-Dateien prüfen |

Eine veröffentlichte Version lässt sich auf npm nur in den ersten 72 Stunden
zurückziehen (`npm unpublish`) und die Versionsnummer danach nie wieder
verwenden; im Zweifel `npm deprecate` und eine neue Version.
