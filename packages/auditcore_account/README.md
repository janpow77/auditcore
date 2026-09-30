# auditcore_account

## Zweck

Gemeinsame Konten, Mandanten, Corporate Design und administrative Zugangsabläufe mit einem Formularvertrag für Vue und React.

Für audit_designer, regulierung und Rechnungslegung. Frameworkfreier Kern mit
Hostanschlüssen für Datenbank, Session, Versand und Bildablage; die Anwendungen
werden in einem späteren Schritt migriert. PDF-Bearbeitung gehört nicht dazu.

## Installation

Version 0.1.1 ist im Arbeitsstand angelegt, noch nicht veröffentlicht.
Lokal nach `auditcore_auth` installieren: `pip install -e packages/auditcore_account`.
Nach Veröffentlichung über den Paketindex:

```bash
python -m pip install 'auditcore_account==0.1.1' \
  --index-url https://janpow77.github.io/auditcore/simple/
```

Hashgebundene Direkt-URL nach Veröffentlichung (Release und SHA-256 aus dem Index):

```text
auditcore_account @ https://github.com/janpow77/auditcore/releases/download/v<release>/auditcore_account-0.1.1-py3-none-any.whl#sha256=<sha256>
```

Das vorgesehene APT-Paket heißt `python3-auditcore-account`; APT-Lebenszyklus und
Veröffentlichung wurden für dieses neue Paket noch nicht ausgeführt.
Extras: `[images]` – Pillow für Bildaufbereitung; `[passwords]` – Argon2-Backend;
`[dev]` – Prüfwerkzeuge und beide Laufzeitextras.

## Schnellstart

```python
from auditcore_account import Actor, AdminService, MemoryRepository, ProfileService, Runtime

runtime = Runtime(MemoryRepository())
account = AdminService(runtime).bootstrap("admin@example.invalid", "Administration")
actor = Actor(account.id, account.session_revision)
profile = ProfileService(runtime).update(actor, "account", account.id, 1, {"title": "Dr."})
assert profile.fields["title"] == "Dr."
assert profile.revision == 2
```

`bootstrap` ist ein einmaliger vertrauenswürdiger Host-Aufruf, keine öffentliche
Route. `MemoryRepository` ist flüchtig und nur eine Referenzablage.

## API-Überblick

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Öffentliche Namen aus `auditcore_account.__all__` (20):

| Name | Art | Kurzbeschreibung (erste Docstring-Zeile) | Modul |
|---|---|---|---|
| `AccountError` | Ausnahme | Fachlicher Fehler mit optionalem Feldbezug. | `errors` |
| `Actor` | Datenklasse | Vom Host authentifizierte Identität und serverseitig geprüfte Sitzungsrevision. | `models` |
| `AdminService` | Klasse | – | `admin` |
| `AssetService` | Klasse | – | `assets` |
| `CredentialsService` | Klasse | – | `credentials` |
| `Crop` | Datenklasse | – | `assets` |
| `Extension` | Datenklasse | – | `schema` |
| `ExtensionRegistry` | Klasse | – | `schema` |
| `FONTS` | Konstante | – | `branding` |
| `Field` | Datenklasse | – | `schema` |
| `Font` | Datenklasse | – | `branding` |
| `ImagePolicy` | Datenklasse | – | `assets` |
| `InvitationService` | Klasse | – | `invitations` |
| `MemoryRepository` | Klasse | Flüchtige Referenz; keine produktive Datenbank und kein impliziter Dateizugriff. | `repository` |
| `ProfileService` | Klasse | – | `profiles` |
| `Repository` | Protokoll | Adapter sichert atomaren Commit, Rollback und serialisierte konkurrierende Zugriffe. | `repository` |
| `Runtime` | Klasse | – | `runtime` |
| `SettingsService` | Klasse | – | `settings` |
| `State` | Datenklasse | – | `repository` |
| `Workspace` | Klasse | – | `workspace` |

Öffentliche Module:

| Modul | Kurzbeschreibung |
|---|---|
| `auditcore_account.admin` | Anlage, Sperren, Mitgliedschaften und delegierbare Rollen. |
| `auditcore_account.assets` | Bilder dekodieren, Metadaten entfernen und als begrenztes PNG neu schreiben. |
| `auditcore_account.branding` | Corporate Design: geprüfter Schriftkatalog, Farben und referenzierte Logo-Varianten. |
| `auditcore_account.credentials` | Passwortwechsel und Sitzungswiderruf über auditcore_auth. |
| `auditcore_account.errors` | Stabile Fehlercodes ohne Geheimnisse oder fremde Kontodaten. |
| `auditcore_account.forms` | JSON-Vertrag des gemeinsamen Vue-/React-Formulars. |
| `auditcore_account.invitations` | Einmalige, gehashte Einladungs-/Reset-Token mit unveränderlichem Text-Snapshot. |
| `auditcore_account.models` | Typisierte Konten, Mandanten und Mitgliedschaften; getrennte Zuständigkeiten. |
| `auditcore_account.permissions` | Mandantengebundene Fähigkeiten; Plattformverwaltung gewährt keine Fachrechte. |
| `auditcore_account.profiles` | Profilzugriff mit Feldrechten und atomarem Versionsvergleich. |
| `auditcore_account.repository` | Transaktionsport und threadsichere Referenzablage für Tests und Einbettung. |
| `auditcore_account.runtime` | Gemeinsame Laufzeit: injizierbare Uhr, Revision und Ereignisse ohne Feldwerte. |
| `auditcore_account.schema` | Explizite Formularfelder und versionierte, typisierte Erweiterungsregistrierung. |
| `auditcore_account.settings` | Versionierte Mandanteneinstellungen und unabhängige Fach-Erweiterungen. |
| `auditcore_account.welcome` | Begrüßung mit sicherer Platzhalterersetzung; kein ausführbarer Vorlagencode. |
| `auditcore_account.workspace` | Gemeinsamer Formularadapter. Host bindet ihn an authentifizierte HTTP-Routen. |
| `auditcore_account.workspace_access` | Zugangsformulare geben Versandaufträge ausschließlich an den vertrauenswürdigen Host zurück. |
| `auditcore_account.workspace_admin` | Administrative Formulare; Rechte werden auch bei direktem Aufruf geprüft. |
<!-- api-overview:end -->

## Profile und Konfiguration

Passwortrichtlinie, Zugangsfristen und Bildgrenzen werden vom Host übergeben.
`ExtensionRegistry` registriert versionierte Fachfelder und deren Rechte.
`SettingsService` verwendet einen freigegebenen Schriftkatalog; Farben werden auf
Textkontrast geprüft. [Integration und Beispiele](docs/integration.md).

## Herkunft und Charakterisierung

Eigenständige Implementierung des gemeinsam erarbeiteten Konten-/Mandantenvertrags.
Fachliche Referenzen: die untersuchten Kontooberflächen von audit_designer,
regulierung und Rechnungslegung; keine Quelltextübernahme. Nachweise und Grenzen
stehen in `src/auditcore_account/provenance.json`. Synthetische Regressionstests
prüfen Rechte, Mandantentrennung, Revisionen, Zugangslinks, Einstellungen und Bilder.
Ein vollständiger Gleichheitsnachweis mit den bisherigen Anwendungen wird nicht behauptet.

## Bewusste Verhaltensabweichungen

Gemeinsame Kontodaten und mandantenabhängige Mitgliedschaftsdaten sind getrennt.
Mandantenadministratoren dürfen keine globalen Passwörter zurücksetzen.
Versionskonflikte brechen Änderungen ab. Einladungen verwenden gehashte Einmallinks;
Corporate Design und Fach-Erweiterungen werden unabhängig gespeichert.

## Abhängigkeiten

Python ≥ 3.11; Pflichtabhängigkeit `auditcore_auth==0.1.1`.
Optional `Pillow>=12.1` für Bilder und `argon2-cffi>=21.1` für Passwörter.
Keine Web-Frameworks, ORM-, PDF- oder Plattformwerkzeuge im Fachkern.

## Sicherheit und Datenschutz

Keine eigenständigen Netzwerkzugriffe. Der Host authentifiziert `Actor`, schützt
Endpunkte mit Session/CSRF/Rate-Limits und implementiert die dauerhafte Ablage.
`WorkspaceResult.delivery` enthält ein Geheimnis und darf nur an den Versandanschluss,
niemals in Formularantworten oder Logs. Garantierter Versand benötigt eine Host-Outbox.
Events enthalten Feldnamen, keine Passwörter oder Profilfeldwerte. Der Host verantwortet
Aufbewahrung, Löschung und Bildauslieferung. [Integrationsvertrag](docs/integration.md).

## Lizenz und Herkunftsnachweis

MIT gemäß [LICENSE](LICENSE); [NOTICE](NOTICE) und
[provenance.json](src/auditcore_account/provenance.json) dokumentieren die eigenständige
Implementierung im auditcore-Projekt. Veröffentlichung wurde nicht vorgenommen.

## Änderungen

[CHANGELOG.md](CHANGELOG.md)
