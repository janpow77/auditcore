# Plugin `auditcore-office`

Claude-Code-Plugin für Office-Makroprojekte (Excel, Access, Word). Es enthält
Abläufe (Skills), Agentenrollen, Hooks und Vorlagen und ruft dafür die CLI
`auditcore-officebank` auf ([Paket](../../packages/auditcore_officebank)). Eigene
Logik enthält das Plugin nicht.

**Stand: Gerüst (Etappe 0).** Skills und Agenten sind Platzhalter mit kurzer
Beschreibung; sie melden nur den Etappenstand. Ausformuliert werden sie in
Etappe 6 laut [Plan](../../docs/projekt/20261005_Plan_auditcore_officebank_0.1.md)
(Kap. 4). Die Marketplace-Datei im Repo-Root folgt ebenfalls in Etappe 6.

## Aufbau

| Pfad | Inhalt | Stand |
|---|---|---|
| `.claude-plugin/plugin.json` | Manifest | vorhanden |
| `skills/<name>/SKILL.md` | 8 Abläufe (Kap. 4.2) | Platzhalter |
| `agents/<rolle>.md` | 6 Agentenrollen (Kap. 4.3) | Platzhalter |
| `hooks/` | 4 Schutz- und Prüf-Hooks (Kap. 4.4) | nur Beschreibung |
| `vorlagen/` | Projektvorlagen (Kap. 4.5) | nur Beschreibung |

## Versionierung

Das Plugin hat eine eigene Version in `plugin.json`. Ab der ersten
ausformulierten Fassung setzt es `auditcore_officebank>=0.1.0` voraus und prüft
das in jedem Skill mit `auditcore-officebank --version`.

## Lizenz

MIT wie das Repository ([LICENSE](../../LICENSE)).
