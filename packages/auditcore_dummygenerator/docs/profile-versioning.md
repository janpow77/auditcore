# Profilversionierung und Freigabevertrag

Das mitgelieferte `profiles.json` bildet die tatsächlich implementierten
Feldregeln, Abweichungsszenarien und DE-/AT-Grunddatenkataloge ab. Jede Regel
hat eine stabile ID, Typ/Titel, Version, Status, echte Zeitstempel der
Metadatenerstellung, Herkunft/Vorgänger, Änderungsgrund und Inhaltshash.
Der Hash bindet den Vertrag an die konkreten Bytes von `generator.py`.
Die ursprüngliche Quellrevision bleibt über Commit/Blob, SHA256 und die
beobachteten Legacy-Fixtures referenziert; sie wird nicht als bereits
veröffentlichte Version dieser neuen Bibliothek ausgegeben.

`owner.repository_owner` und `authors.source_commit_author` sind beobachtete
GitHub-Angaben. Eine Organisation wurde nicht belegt und bleibt `UNKNOWN`.
Der neue Metadatensatz wurde von Codex erstellt; damit wird weder eine
Organisation noch eine fachliche menschliche Freigabe behauptet.

## Draft, Review und Release

Die Profile sind jetzt **Draft**. Während der technischen Bearbeitung dürfen
Drafts geändert werden; Änderungen müssen in Git nachvollziehbar sein und
Hash, Änderungszeit und Änderungsgrund aktualisieren. Frühere Source-Commits
und beobachtete Golden-Fixtures werden nicht überschrieben. Technischer
Review umfasst Quellvergleich, alle bekannten Characterization-Fälle,
Metadaten-/Hashprüfung und ausdrücklich dokumentierte technische Korrekturen.
Der Metadatenstatus allein ersetzt keinen ausgeführten Prüfbericht.

Ein Release erfordert eine dokumentierte Entscheidung des zuständigen
Projektverantwortlichen mit Identität, Datum, betroffener Version und
Artefakthash. Quellrechte müssen davor geklärt sein. Aktuell existiert keine
solche Releaseentscheidung; `NOT_GRANTED` bezeichnet diesen Stand und keine
angebliche Ablehnung. Draft-Tests setzen keine menschliche Freigabe voraus.

Freigegebene Versionen werden als versionierte Wheels/sdists zusammen mit
SBOM und Manifest unveränderlich archiviert. Eine veröffentlichte
Paket-/Profilversion darf nicht mit anderem Inhalt ersetzt werden. Jede
fachliche Änderung erzeugt eine neue Profil- und Paketversion mit
Vorgängerbezug; bestehende Artefakte und Tests bleiben abrufbar. Ein Rollback
installiert die vorherige unveränderte Version. Bei technischer Änderung
ohne fachliche Änderung wird ebenfalls eine neue Paketversion erstellt.
Force-Push und History-Rewrite sind kein Versionierungsverfahren.

Vor Freigabe vergleicht der Reviewer die neuen Profile und den Quell-Diff
mit dem vorherigen archivierten Manifest. Konflikte in fachlichen Regeln
werden als menschliche Entscheidung dokumentiert. Der Bibliotheksbuild
selbst ist ausdrücklich kein Release. Öffentliche Veröffentlichung ist
bei ungeklärten Quellrechten gesperrt.

## Exakte Referenzen für Läufe

`list_profiles()` liest frische Metadaten und prüft deren Inhalts- und
Implementierungshashes. `profile_reference(artifact_id)` liefert die genaue
Version und beide Hashes. Ein Consumer speichert diese Referenz zusammen
mit Request-/Outputhash, Seed, Bezugsdatum, Workerzahl, Backend und
Pythonversion in seinem eigenen Run-Manifest. Die Bibliothek schreibt keine
heimlichen Logdateien und verändert für Metadaten nicht das bisherige
Zeilenformat.

```python
from auditcore_dummygenerator import profile_reference

reference = profile_reference("auditcore.dummygenerator.field.amount_eur")
# reference zusammen mit den tatsächlich verwendeten Requestparametern speichern
```

Eigene gewichtete Listen, Parameter oder zusätzliche Szenarien des Consumers
gehören zu dessen versioniertem Profil. Das Paketregister behauptet nicht,
diese unbekannten externen Inhalte zu verwalten. Es enthält keine Prompts
oder Agenten; Prompt-/Agent-spezifische Diff-, Such- und Toolrechtetests sind
für diese Profile nicht anwendbar.
