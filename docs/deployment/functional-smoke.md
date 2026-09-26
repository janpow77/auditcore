# Fachlicher Rauchtest nach jedem Produktions-Deploy (Pflicht)

**Regel (Rechteinhaber, 24.09.2026: „das soll pflicht sein“):** Nach jedem
Deploy außerhalb der internen Testumgebung wird mindestens eine geänderte
Funktion über die echte API der laufenden Anwendung aufgerufen und ihr
fachliches Ergebnis geprüft. Ein grüner Deploy-Workflow oder ein
Health-Endpunkt mit HTTP 200 gilt **nicht** als getestet.

Die Regel ist im Code durchgesetzt, nicht nur hier beschrieben:

| Stelle | Wirkung |
|---|---|
| `auditcore.tools.deployer.smoke.load_cases` | lehnt leere Definitionen, Health-/Readiness-Pfade, Fälle ohne geprüfte Funktion (`changed_feature`) oder ohne fachliche Erwartung ab; schreibende Fälle müssen Testdaten mit `AUDITCORE-SMOKE` markieren |
| `auditcore-deploy plan` | `BLOCKED` für jedes `deployment_target` außer `internal_test`, solange keine gültigen `functional_smoke`-Fälle im Profil stehen |
| `auditcore-deploy smoke <config> --base-url https://…` | führt die Fälle aus, schreibt `.auditcore/functional-smoke.json` (ohne Antwortinhalte und ohne Zugangsdaten) und endet mit Exitcode 1, wenn ein Fall nicht `PASS` ist oder Zugangsdaten fehlen (`NOT_CONFIGURED`) |
| `.github/actions/functional-smoke` | wiederverwendbare Action für die Deploy-Workflows der Anwendungen |

## Fälle definieren

In `auditcore-deploy.json` oder einer eigenen JSON-Datei:

```json
{
  "functional_smoke": [
    {
      "name": "sanktionsabgleich",
      "changed_feature": "Sanktionsabgleich über auditcore_registry_sources",
      "path": "/api/sanctions/search?q=Testname",
      "headers_from_env": {"Authorization": "SMOKE_AUTHORIZATION"},
      "json_expect": {"lists": {"contains": "EU"}, "results": {"exists": true}}
    },
    {
      "name": "dokumentvergleich",
      "changed_feature": "Dokumentvergleich (auditcore_documents, Profil CORRECTED)",
      "method": "POST",
      "path": "/api/document-comparisons",
      "json_body": {"title": "AUDITCORE-SMOKE-Vergleich"},
      "expected_status": 201,
      "json_expect": {"metadata.profile": {"contains": "CORRECTED"}}
    }
  ]
}
```

- `json_expect`: Punktpfad → erwarteter Wert oder `{"exists": true}`,
  `{"contains": "…"}`, `{"min": …, "max": …}`. Alternativ `body_contains`.
- Zugangsdaten nur über `headers_from_env` (Name der Umgebungsvariable); Werte
  werden weder ausgegeben noch gespeichert.
- Testdaten synthetisch, mit `AUDITCORE-SMOKE` markiert, nach dem Test über die
  API entfernen, soweit die Anwendung das zulässt.

## Im Deploy-Workflow der Anwendung

```yaml
      - name: Fachlicher Rauchtest (Pflicht)
        uses: janpow77/auditcore/.github/actions/functional-smoke@<commit>
        env:
          SMOKE_AUTHORIZATION: ${{ secrets.SMOKE_AUTHORIZATION }}
        with:
          base-url: https://app.example
          config: deploy/functional-smoke.json
```

Der Deploy gilt erst als abgeschlossen, wenn dieser Schritt grün ist. Für jede
Anwendung wird dafür ein eigener, eng berechtigter Rauchtest-Zugang (Service-
Konto oder Token nur für die Testfälle) angelegt; persönliche Admin-Zugänge
werden nicht verwendet.
