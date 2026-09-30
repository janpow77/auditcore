# auditcore_account

Gemeinsamer, frameworkfreier Kern für persönliche Konten, Mandanten und Administration.
Version **0.1.0**. Die native Vue- und React-Oberfläche liegt in den bestehenden
Paketen `@auditcore/ui` und `@auditcore/ui-react`; beide verwenden `@auditcore/ui-core`.

## Enthalten

- Persönliche Namen und Profilbild; Funktion und dienstliche Kontaktdaten je Mitgliedschaft.
- Mandantenstammdaten, Status, Mitgliedschaften und delegierbare Rollen.
- Plattformadministration, Kontosperre und Widerruf bestehender Sitzungen.
- Passwortwechsel mit `auditcore_auth`, befristete Startpasswörter mit Wechselpflicht,
  gehashte Einmallinks für Einrichtung und Reset. Externe Identitäten bleiben extern verwaltet.
- Begrüßung mit begrenzten Platzhaltern, sicherem Klartext-/HTML-Renderer,
  Versand-Snapshot und quittierbarem ersten Besuch je Mitgliedschaft.
- Corporate Design: Logo-Varianten, Farben mit Kontrastprüfung, freigegebener Schriftkatalog,
  Dokumentkopf und -fuß. Dateibasierte Schriftinstallation erfolgt im Host.
- Unabhängig versionierte Fach-Erweiterungen mit Feldschema, Validator und Lese-/Schreibrechten.
- Begrenztes, neu kodiertes Bildformat ohne übernommene Metadaten, temporäre Uploads,
  Vorschaubilder und Bildzuschnitt. JPEG, PNG und WebP; keine aktiven SVG-Inhalte.
- Atomare Änderungen, erwartete Revisionen und Ereignisse ohne Passwort- oder Feldinhalte.
- Gemeinsamer JSON-Formularadapter `Workspace` für beide Frontends.

## Installation und Einstieg

```bash
pip install 'auditcore_account[images,passwords]==0.1.1'
```

Im Monorepo zuerst `auditcore_auth` und dann dieses Paket installieren. Der
Host gibt Passwortrichtlinie, Gültigkeitsdauern und Bildgrenzen ausdrücklich vor.
Es gibt keine versteckten fachlichen Standardfristen.

```python
from datetime import timedelta
from auditcore_account import (
    Actor,
    AdminService,
    CredentialsService,
    MemoryRepository,
    ProfileService,
    Runtime,
    SettingsService,
    Workspace,
)

runtime = Runtime(MemoryRepository())  # flüchtige Demoablage
admin = AdminService(runtime)
initial = admin.bootstrap("admin@example.invalid", "Administration")
actor = Actor(initial.id, initial.session_revision)


# Im Host: eigene verbindliche Passwortprüfung übergeben.
def validate_password(password: str) -> None:
    if len(password) < 15:
        raise ValueError("Passwortrichtlinie der Beispielanwendung nicht erfüllt.")


credentials = CredentialsService(runtime, validate_password)
workspace = Workspace(
    ProfileService(runtime),
    SettingsService(runtime),
    admin,
    credentials,
    access_lifetime=timedelta(hours=1),  # Beispielkonfiguration, keine Fachvorgabe
)
form = workspace.read(actor, "profile")
result = workspace.save(actor, "profile", form["revision"], {"title": "Dr."})
assert result.document["values"]["title"] == "Dr."
```

`bootstrap` ist ein einmaliger, vertrauenswürdiger Einrichtungsaufruf. Er gehört
nicht in eine öffentlich erreichbare Route. Das lokale Passwort wird danach
über `credentials.provision` initialisiert und beim ersten Login geändert.
`Actor` wird ausschließlich aus der serverseitig geprüften Anmeldung erstellt.

## Integrationsvertrag

`Repository.transaction()` muss Commit/Rollback und konkurrierende Änderungen
serialisieren. `MemoryRepository` ist eine Referenz für Tests und Demos, keine
produktive Datenbank. Ein Datenbankadapter muss die gesamte gelesene und veränderte
Einheit atomar behandeln; ein ungesperrtes „Laden und später Überschreiben“ genügt nicht.
Dauerhafte Datenbank-, Dateiablage- und Migrationsadapter werden beim Anschluss der
Anwendungen implementiert. Keine bestehenden App-Daten werden automatisch migriert.

`Workspace.list(actor, tenant)` liefert die Navigation; `read(actor, id, tenant)`
das Formular; `save(actor, id, revision, values, tenant)` ein `WorkspaceResult`.
Die Reihenfolge der Parameter unterscheidet sich bewusst von `SettingsService.save`:
am HTTP-Rand benannte Argumente verwenden.

Der Host gibt **nur `result.document`** an den Browser zurück. `result.actor`
übernimmt er nach Passwortwechsel in eine neu ausgestellte Sitzung. Bei
`result.reauthenticate` beendet er die Sitzung. `result.delivery` geht ausschließlich
an den vertrauenswürdigen Versandanschluss; Token dürfen weder in Logs noch in
normalen Formularantworten landen. Für garantierten Versand braucht der Host eine
transaktionale Outbox, die den Auftrag sicher speichert; dies ist keine Zusicherung
von `MemoryRepository`. Das Speichern des Begrüßungstextes versendet nichts.

Die Plattform darf globale Zugänge verwalten. Ein Mandantenadministrator darf
keine globalen Passwörter anderer Konten zurücksetzen und keine fremden Konten
lesen. Für neue globale Nutzer ist die Plattform zuständig; Mandantenadministratoren
können vorhandene Konten über ihre Anmeldekennung zuordnen. Fachrechte werden nur
über explizite Rollen vergeben; Plattformrechte gewähren sie nicht automatisch.
Mindestens eine aktive Plattformadministration muss erhalten bleiben.

Der Host ergänzt seine bestehenden Session-/SSO-Verfahren, MFA, CSRF, Rate-Limits,
Uploadlimits vor dem Einlesen, Versand und sichere Auslieferung der Bilder.
Passwort- und Reset-Endpunkte gehören hinter diese Schutzmaßnahmen.
`CredentialsService.login` ist keine vollständige Web-Anmeldung.

Uploads gehen über `AssetService.upload` und werden erst beim Profilspeichern
zugeordnet. Bilder werden über autorisierten Zugriff ausgeliefert, nicht über
öffentliche Dateipfade. Abgelaufene Uploadentwürfe entfernt `purge_drafts`.
Ersetztes Bildmaterial und personenbezogene Daten löscht der Host nach seiner
Aufbewahrungsregel; es gibt keine pauschale automatische Kontolöschung.

## Fach-Erweiterungen

```python
from auditcore_account import Extension, ExtensionRegistry, Field

registry = ExtensionRegistry()
registry.register(
    Extension(
        id="rechnungslegung.programm",
        version=1,
        title="Operationelles Programm",
        fields=(Field("cci", "CCI", required=True), Field("name", "Programmbezeichnung")),
        read_permission="programm.read",
        write_permission="programm.write",
        validate=validate_programme,  # eigener Validator der Anwendung
    )
)
```

`SettingsService(runtime, registry)` verwendet die Registrierung;
`AdminService(runtime, frozenset({"programm.read", "programm.write"}))` registriert
zusätzliche delegierbare Berechtigungen. Persistierte Werte sind Textfelder;
komplexe Daten benötigen einen anwendungseigenen Validator/Codec. Unbekannte Felder
werden abgelehnt; fremde Erweiterungen und deren Daten bleiben unverändert.
Ein Versionswechsel erfordert eine ausdrücklich implementierte Datenmigration.

## Prüfung und Oberfläche

Vom Repository-Root mit aktivierter Entwicklungsumgebung:

```bash
auditcore-runner lokal account --host --ohne-cache
```

Weitere Details: [gemeinsame Oberfläche](../../../docs/ui/account.md),
[fachlicher Entwurf](../../../docs/ui/konto-mandant-best-practice.md).
Die PDF-Bearbeitung ist ein eigenständiges Vorhaben und keine Abhängigkeit dieses Pakets.
