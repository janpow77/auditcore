# Nachweise für F-09 und F-15 im Fachkern

Stand: 22. September 2026. Geprüfter Implementierungscommit:
`8d04fc3e128b1ddd03e90a2ebbac4ca0da94a483`.
Geltungsbereich: die sieben Python-Dateien unter `src/auditcore` ohne
`auditcore.tools`; Kontext: [contexts/core.json](../../contexts/core.json).
Dieser Nachtrag ist weder eine Freigabe der Werkzeuge noch einer Fachanwendung.

Maßgebliche Quelle ist `janpow77/verwaltung-app-framework`, Commit
`15f5338f783f2c7d5760a9bb299be06d27326be0`: insbesondere
[Verbindlichkeitsmatrix](https://github.com/janpow77/verwaltung-app-framework/blob/15f5338f783f2c7d5760a9bb299be06d27326be0/docs/verbindlichkeit.md),
[Prüfkatalog](https://github.com/janpow77/verwaltung-app-framework/blob/15f5338f783f2c7d5760a9bb299be06d27326be0/docs/pruefkatalog.md)
und [Artefaktanforderungen](https://github.com/janpow77/verwaltung-app-framework/blob/15f5338f783f2c7d5760a9bb299be06d27326be0/docs/kollaborative-artefakte.md).
Die Aktualität wird im beigefügten Policy-Lauf gegen GitHub geprüft.
F-09 und F-15 sind eigene Framework-Architekturanforderungen; diese Bewertung
behauptet keine Zertifizierung oder vollständige Erfüllung externer Normen.

## F-09: Architektur und Änderungsgrenzen

**Belegt im genannten Fachkernumfang.** F-09 bezeichnet Architektur, nicht
Datenschutz; Datenschutz und DSFA gehören insbesondere zu F-05.

Der Fachkern stellt Datenklassen, Fehlerklassen, übergebene versionierte
Regelparameter und eine reine Zahlenformatfunktion bereit. Er enthält weder
Benutzerverwaltung noch Rechtevergabe, Mandantenpersistenz, Freigabedienst oder
Zugriff auf eine geschützte Datenhaltung. Seine sieben Dateien wurden vollständig
gelesen. Die erneute AST-Prüfung erfasst alle Imports: ausschließlich Python-
Standardbibliothek und die eigene Formatfunktion. Der Architekturprüfer meldet
keine Framework-, Infrastruktur- oder Tool-Abhängigkeit. Die exakten Dateien,
Hashes und Imports stehen in [core-verification.json](core-verification.json).

Die Schnittstellengrenze lautet: Ein Consumer autorisiert den Zugriff auf seine
Daten **vor** dem Aufruf des Fachkerns und führt Freigabe, Speicherung und
Auditierung in seiner eigenen dafür vorgesehenen Schicht aus. Ein `PASS` oder
`ValidationResult.valid` ist ausschließlich ein fachliches Prüfergebnis und
erteilt keine Benutzerberechtigung oder verbindliche Freigabe. `SourceReference`
und `ProvenanceRecord` transportieren Herkunft; sie ersetzen keine
manipulationsgeschützte Audit-Historie einer Anwendung.

Damit ist T-38 für diesen Umfang tatsächlich durch Quellreview und ausführbare
Architekturprüfung abgedeckt: Es gibt keinen direkten Persistenzzugriff und
keine Änderung oder Umgehung vorhandener Rechte-/Freigabemechanismen im Fachkern.
Die negativen Architekturtests prüfen zusätzlich Frameworkimporte,
Infrastrukturimporte, Toolimporte sowie dynamische und relative Importformen.
Die ausgeführte Kombination aus Core-, Reporting- und Quality-Tests besteht aus
70 erfolgreichen Testfällen. Dies bestätigt keine ungetestete Consumer-Anbindung.

Änderungen an den erfassten Dateien, neue Fachmodule, eigene Ein-/Ausgabe oder
ein anderer Anwendungskontext erfordern eine neue Bewertung. Der Nachweis ist
an die Dateihashes gebunden; der Framework-Provider allein erzwingt diese
Artefaktbindung derzeit nicht. Deshalb wird die Nachweisdatei nicht pauschal
als `.auditcore/policy-evidence.json` für alle Werkzeuge installiert.

## F-15: Versionierte teilbare Fachartefakte

**Teilweise belegt; REVIEW_REQUIRED bleibt bestehen.**
`versioned_artifacts=true` bleibt unverändert: `RuleSet` enthält ausdrücklich
versionierte fachliche Regeln. Die vorhandenen `frozen`-Datenklassen,
Versions-/Quellenangaben, Provenienz und Git-Historie sind vorhandene Bausteine.
Unveränderlichkeit einer Python-Datenklasse ist jedoch noch kein Schutz
veröffentlichter Artefaktversionen.

| Aspekt | Tatsächlicher Stand | Nächster notwendiger Schritt |
|---|---|---|
| Regelversion, Quelle, Gültigkeitsbeginn | `RuleSetMetadata` vorhanden und Core-Test ausgeführt | Eindeutige Artefakt-ID und Bezug zur vorherigen Version festlegen |
| Herkunft einer extrahierten Funktion | `ProvenanceRecord` und Reporting-Provenienz vorhanden | Für Fachregelversionen den passenden Herkunfts-/Fork-Vertrag ergänzen |
| Autor/Eigentümer, Organisation, Erstellungs-/Änderungszeit, Status, Änderungsgrund, Inhaltshash | Nicht vollständig im Regelartefakt modelliert | Metadaten ergänzen und in einem realen Versionswechsel prüfen |
| Frühere veröffentlichte Fassungen bleiben abrufbar | Git-Quellen sind revisionsbezogen abrufbar; kein vollständiger Release-/Regelarchivnachweis | Speichermodell und unveränderliche Veröffentlichung technisch prüfen |
| Fachlich lesbarer Vergleich von Regelversionen | Kein eigener strukturierter Regelvergleich nachgewiesen | Metadaten- und Parameteränderungen reproduzierbar vergleichen und testen |
| Review und geschützte Veröffentlichung | Keine zuständige fachliche Releaseentscheidung dokumentiert | Projektverantwortung legt fest, welche Zustände eine verbindliche Freigabe darstellen und wer prüft; danach technische Grenzen testen |
| Prompts/Agenten, Prompt-Suche, KI-Läufe | Nicht Bestandteil des hier abgegrenzten Fachkerns | Werkzeuge separat bewerten; keine Übertragung eines Core-Nachweises |

T-26 bis T-28 sind im aktuellen generischen Adapter wegen
`versioned_artifacts=true` anwendbar, obwohl diese konkreten Tests Prompt-Diffs,
Prompt-Suche beziehungsweise Agent-Forks beschreiben.
Der Fachkern implementiert diese Funktionen nicht. Das ist eine dokumentierte
Granularitätslücke im Test-Adapter, kein Grund, `versioned_artifacts=false` zu
setzen oder die Tests als bestanden auszugeben. Eine spätere Adapteränderung
muss Artefaktarten explizit unterscheiden und F-15-Nachweise für Regelwerke
beibehalten. Im unveränderten Provider bleiben diese Tests `NOT_EXECUTED`.
T-29 berücksichtigt zusätzlich die KI-Nutzung und ist für den Core-Kontext
bereits `NOT_APPLICABLE_WITH_REASON`.

## Nachweisstatus und Reproduktion

[core-evidence.json](core-evidence.json) enthält den belegten F-09-Nachweis
und die offenen F-15-Referenzen. [core-policy-evaluation.json](core-policy-evaluation.json)
ist das tatsächlich erzeugte Provider-Ergebnis für genau diesen Core-Kontext:
F-09 `VERIFIED`, F-15 weiter `REVIEW_REQUIRED`, Gesamtstatus `REVIEW_REQUIRED`.
Der Provider führt Testfälle nicht selbst aus und markiert auch T-38 weiterhin
`NOT_EXECUTED`; dessen separat ausgeführter Nachweis steht in
`core-verification.json`. Diese unterschiedlichen Nachweisarten werden nicht
durch nachträgliches Ändern des Provider-Berichts vermischt.

Erneute fachliche Bewertung mit expliziter Nachweisübergabe:

```python
import json
from dataclasses import asdict
from pathlib import Path

from auditcore.tools.policy import ApplicabilityContext, GitFrameworkPolicyProvider

evidence = json.loads(Path("docs/policy/core-evidence.json").read_text())
context = ApplicabilityContext.from_dict(json.loads(Path("contexts/core.json").read_text()))
provider = GitFrameworkPolicyProvider(
    evidence=evidence,
    artifact="auditcore.core",
)
result = provider.evaluate(context)
print(json.dumps(asdict(result), indent=2))
```

Vor Wiederverwendung des F-09-Nachweises müssen die Dateihashes aus
`core-verification.json` mit dem zu bewertenden Quellstand übereinstimmen.
Tests erneut ausführen:

```bash
.venv/bin/pytest tests/test_core.py tests/test_reporting.py tests/test_quality.py -q
```

Offene menschliche Entscheidung ist insbesondere der fachliche Review- und
Veröffentlichungsvertrag für Regelwerke. Fehlende Metadaten, Versionsvergleich
und Historienprüfungen sind dagegen technische Arbeit und werden nicht als
pauschale Genehmigungsblockade dargestellt. Der technische Architekturbeleg
für F-09 benötigt keine erfundene menschliche Datenschutz-/Betriebsfreigabe.
