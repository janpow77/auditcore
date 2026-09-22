# Framework-Nachweise: Artefaktbindung und genaue Anwendbarkeit

Stand: 22. September 2026. Umsetzung für Phase A/B des
[Implementierungsplans](../architecture/IMPLEMENTATION_PLAN.md).
Keine Fachbibliothek und keine reale Consumer-Anwendung wurde hierfür geändert.

Die maßgebliche Framework-Quelle wurde erneut gegen GitHub geprüft:
`janpow77/verwaltung-app-framework`, HEAD
`15f5338f783f2c7d5760a9bb299be06d27326be0`.
Die vorhandenen Quell- und Tabellenhashes bleiben erhalten. Änderungen an den
Quellen führen weiterhin zu unbekannter Adapteranwendbarkeit beziehungsweise
`POLICY_SOURCE_STALE`; MUSS, BEDINGT und SOLL behalten ihre Bedeutung.

## 1. Ein Nachweis gehört zu einem konkreten Artefaktstand

Ein `VERIFIED`-Eintrag wird nur dann als `PASS` ausgewertet, wenn alle folgenden
Angaben zur aktuellen Prüfung passen:

- `source_commit`: verwendeter Framework-Commit;
- `artifact`: explizite Identität des geprüften Pakets oder Projekts;
- `artifact_source_digest`: frisch berechneter SHA-256 des geprüften Quellbaums;
- `context_digest`: SHA-256 des vollständigen aktuellen `ApplicabilityContext`;
- `references`: nichtleere Liste konkreter Nachweisreferenzen.

Das gilt auch für `IMPLEMENTED` und `MISSING`: Fremde oder veraltete
Negativnachweise dürfen keinen unbegründeten Compliance-Fehler auslösen.
Fehlende oder abweichende Angaben ergeben `EVIDENCE_INVALID` mit Gate
`REVIEW_REQUIRED`. Ohne lesbaren `artifact_root` wird kein solcher Nachweis
akzeptiert. Änderungen an Code, Konfiguration, Ressourcen oder Anwendbarkeit
entwerten die bisherige Bindung. Für genehmigte Abweichungen gelten zusätzlich
zu den bisherigen Zuständigkeits-/Begründungsfeldern dieselben drei
Artefaktbindungsfelder; alte oder fremde Abweichungen bleiben
`DEVIATION_PENDING`.

Die Prüfung erfolgt nach der Anwendbarkeitsbestimmung. Nicht anwendbare
Anforderungen werden weiterhin begründet ausgeschlossen; ein fehlender Beleg
erzeugt dafür keinen künstlichen Fehler. Ein nachgewiesener Einzelpunkt
ersetzt weder weitere anwendbare Framework-Tests noch eine Betriebsfreigabe.

### Quellumfang

`artifact_source_digest(root)` berücksichtigt relative Dateipfade und alle
Dateiinhalte, einschließlich nicht aus Python bestehenden Ressourcen und
Konfiguration. Generierte Zustände werden ausgeschlossen: `.auditcore`, `.git`,
virtuelle Umgebungen, übliche Python-Test-/Typ-/Lint-Caches, `node_modules`,
`*.egg-info`, Bytecode und Coverage-Ausgaben. `build` und `dist` werden nur
direkt unter dem Artefaktroot ausgeschlossen; gleichnamige echte Module unter
`src` bleiben Bestandteil des Nachweises.

Prüfprotokolle und die Nachweisdateien selbst gehören nach `.auditcore`, damit
das Schreiben eines Protokolls keinen selbstbezüglichen Hash erzeugt.
Produktive Konfiguration und ausgelieferte Ressourcen gehören in den erfassten
Quellumfang. Externe Dateisymlinks, Verzeichnissymlinks, nichtreguläre Dateien,
unlesbare Quellbereiche oder ein leerer Quellbaum ergeben keine gültige Bindung.
Interne Dateisymlinks werden einschließlich der Zielbytes erfasst.

`evaluate_project(root)` liest bei **jedem** Aufruf ausschließlich die aktuellen
Dateien `.auditcore/policy-evidence.json` und `.auditcore/policy-decisions.json`.
Es gibt keinen Fallback auf zuvor global gesetzte Provider-Nachweise. Gelöschte
oder geleerte Nachweisdateien können deshalb keine alte Freigabe reaktivieren.

### Schnittstelle für technische Prüfläufe

```python
from pathlib import Path

from auditcore.tools.common import write_json
from auditcore.tools.policy import GitFrameworkPolicyProvider, evidence_binding
from auditcore.tools.policy.framework import context_from_project

root = Path("technical-consumer-fixture")
context = context_from_project(root)
provider = GitFrameworkPolicyProvider(
    artifact="synthetic.consumer",
    artifact_root=root,
)
source = provider.load_requirements()

# Erst NACH tatsächlich ausgeführtem, dokumentiertem F-09-Nachweis schreiben.
# Dieses Beispiel ist eine Schreibschnittstelle, kein ausgeführter Nachweis.
record = {
    "status": "VERIFIED",
    "source_commit": source.commit_sha,
    **evidence_binding(root, "synthetic.consumer", context),
    "references": [".auditcore/architecture-test-result.json"],
}
write_json(root / ".auditcore/policy-evidence.json", {"F-09": record})
result = provider.evaluate_project(root)
```

`evidence_binding(root, artifact, context)` erzeugt **nur Bindungsdaten**, keinen
fachlichen Prüferfolg und keine menschliche Freigabe. Der aufrufende Prüflauf
muss den benannten Nachweis tatsächlich ausführen und dessen Umfang bewerten.
Eine synthetische Testfixture ist ausdrücklich entsprechend zu kennzeichnen.
Das Format bietet Integritäts- und Geltungsbereichsprüfung, keine digitale
Signatur oder Authentifizierung einer menschlichen Genehmigung.

Nach einer Migration müssen Tests und anwendbare Nachweise für den veränderten
Stand erneut ausgeführt und gebunden werden. Ein unveränderter alter
`VERIFIED`-Eintrag darf eine Codeänderung nicht automatisch freigeben. Direkte
Aufrufe von `evaluate(context)` können Nachweise weiterhin explizit am Provider
übergeben, benötigen aber ebenfalls `artifact_root` und die aktuelle Bindung.

## 2. Regelwerke sind keine Prompt-Registry

Das neue optionale Kontextfeld `versioned_artifact_types` erfasst eine explizite
Liste aus `prompt`, `agent`, `rulebook`, `checklist`, `strategy`, `template` und
`notebook_template`. Nicht angegebene Werte bleiben `UNKNOWN`; die Typen werden
nicht aus dem Paketnamen geraten. Beispiel für einen reinen Regelwerkskern:

```json
{
  "versioned_artifacts": true,
  "versioned_artifact_types": ["rulebook"]
}
```

Bei `versioned_artifacts=true` benötigt die MUSS-Umfangsklärung F-15.ASSESS
jetzt auch bekannte Artefaktarten. F-15 selbst bleibt für alle versionierten
Fachartefakte anwendbar und benötigt weiterhin passende Versions-, Herkunfts-,
Review- und Historiennachweise.

Die konkreten Tests folgen ihrem tatsächlichen Quellumfang:

| Framework-Test | Zusätzlicher Auslöser |
|---|---|
| T-26: Prompt-Diff | `prompt` |
| T-27: Prompt-Suche/Metadaten | `prompt` |
| T-28: Prompt-/Agent-Fork und Toolrechte | `prompt` oder `agent` |
| T-29: Vergleich zweier Prompt-Versionen mit Modell | `prompt` und anwendbare KI-Nutzung |

Regelwerke allein lösen keine Prompt-Suche aus. Fehlende Angaben ergeben
`REVIEW_REQUIRED`, keine stillschweigende Nichtanwendbarkeit. Unbekannte
Testanwendbarkeit fließt jetzt auch in `review_required` und den Gesamtstatus
ein. Der Provider führt diese Tests nicht selbst aus: Anwendbare Tests bleiben
bis zur getrennten tatsächlichen Durchführung `NOT_EXECUTED`.

## 3. Tatsächliche Verifikation und Grenzen

Gezielte Regressionen prüfen gültige Bindungen, andere Artefakte, veränderte
Kontexte, fehlende/falsche Quellhashes, Code-/Ressourcenänderungen, unlesbare
Grenzen, Symlinks, geleerte/gelöschte Projektbelege und ungültige Referenzen.
Weitere Fälle unterscheiden Regeln, Prompts, Agenten, gemischte und unbekannte
Artefaktarten. Technische Prüfbefehle:

```bash
.venv/bin/pytest tests/test_policy.py tests/test_quality.py -q
.venv/bin/ruff check src/auditcore/tools/policy tests/test_policy.py
.venv/bin/mypy src/auditcore/tools/policy
```

Alle drei Befehle wurden erfolgreich ausgeführt. Der gezielte Testlauf umfasst
76 bestandene Fälle. Diese Aussage gilt für die Policy-/Quality-Regression;
vollständige Plattform-, Migrations- und Installationstests bleiben gesonderte
Integrationsnachweise des Hauptprüflaufs. Ältere Core-Nachweisdateien ohne neue
Bindungsfelder bleiben historische Dokumentation und werden nicht nachträglich
als gültige aktuelle Freigaben ausgegeben.
