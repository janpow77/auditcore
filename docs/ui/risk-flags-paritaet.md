# Paritätsinventur Risiko-Merkmale (Red Flags) – Oberfläche

Stand 2026-09-25. Grundlage für die wiederverwendbaren Komponenten in
`@flowaudit/ui` (`packages-js/ui/src/risk/`, Web Component
`<flowaudit-risk-flags>`, React-Hülle in `@flowaudit/ui-react`) und den
REST-Vertrag [risk-rest.md](risk-rest.md). Untersucht wurden die bestehenden
Oberflächen der drei Anwendungen, deren Regeln `auditcore_risk` als Profile führt.

## Bestand in den Anwendungen

### riskanalysis (Vue 3, `frontend/src/verwk/`)

Profil `riskanalysis.year_bound` 2026.09.5 (Branch `feat/auditcore-v0.3.0`,
`backend/app/pipeline/red_flags.py`, Doku `docs/RED_FLAG_EINGABEFELDER.md`).

| Fundstelle | Fähigkeit |
|---|---|
| `views/Overview.vue` („Red Flags (Beleg-Ebene)“) | Kachel je Code mit Trefferzahl, Code und Bezeichnung aus `red_flag_summary` (`code`, `bezeichnung`, `treffer`); kein Anteil, kein Volumen, keine unbestimmten Belege sichtbar |
| `views/Belege.vue` | Belegtabelle mit Spalte „Red Flags“ (`red_flag_codes`), Filter per Query `?red_flag=RF08` (Titel „Red Flag RF08“) |
| `views/Beleg.vue` | Einzelbeleg: Codes als Pillen (`vk-pill hoch`), sonst „keine Red Flags“; keine Begründung, keine Werte, keine Schwellen |
| Backend `red_flags.py` | Spalte `red_flag_unbestimmt` („RF02: Nettobetrag fehlt in der Quelle \| RF08: …“), Summary mit `unbestimmt` und `unbestimmt_begruendung` (Grund → Anzahl) – **in der Oberfläche noch nicht angezeigt** |
| `docs/RED_FLAG_EINGABEFELDER.md` | Tabelle Quelle → Feld → Regeln → Pflicht/optional → Folge bei fehlender Spalte (z. B. ohne `nettobetrag` RF02/RF08 unbestimmt, kein Rückfall auf brutto) |

### flowinvoice (React 18, `frontend/src/components/`)

Profile `flowinvoice.risk_checker`, `flowinvoice.rbvk_wibank`,
`flowinvoice.exante_*` sowie Betrugsprüfung (`fraud_signals`, `ted_contractor`,
`duplicates`).

| Fundstelle | Fähigkeit |
|---|---|
| `risk-wheel/RiskDetailCard.tsx`, `RiskDetailList.tsx` | aufklappbare Karte je Kategorie (`aria-expanded`), Zähler je Schwere, Einträge gruppiert nach Dokument, Begrenzung auf 50 Einträge mit Hinweis „weitere“ |
| Schwerestufen | `critical` (violett), `high` (rot), `medium` (bernstein), `low` (grün), `info` (blau); Beschriftung „Kritisch/Hoch/Mittel/Niedrig/Info“ |
| `fraud-report/RiskScoreBreakdown.tsx`, `RiskScoreGauge.tsx` | Score-Aufschlüsselung je Faktor als gestapelter Balken, Tabelle mit Summenzeile, Stufenbänder |
| `fraud-report/ExecutiveSummary.tsx`, `Recommendations.tsx`, `ExplainPanel.tsx` | Zusammenfassung, Empfehlungen, Erklärung je Befund (`description`/`evidence`/`recommendation` aus `messages`) |
| `fraud-report/DuplicateSection.tsx`, `TEDAnalysisSection.tsx`, `SanctionsCheck.tsx` | Fachsichten der Betrugsprüfung (außerhalb des Red-Flag-Kerns) |
| Export | PDF, Word, HTML (`usePdfExport`, `useWordExport`, `useHtmlExport`) |

### audit_designer – FlowStat-Belegliste

Profil `audit_designer.flowstat_belegliste` (BL_RF01–BL_RF10).

| Fundstelle | Fähigkeit |
|---|---|
| `backend/app/modules/flowstat/services/belegliste_analysis_service.py` (`_red_flags`) | liefert nur die Zusammenfassung (`code`, `count` bzw. `share` für BL_RF10) |
| `frontend/src/modules/flowstat/…` | generische Analyseansicht der Belegliste; keine Anzeige je Beleg, keine Begründung |
| `components/vba/VbaDatenManager.vue` | Reiter „Red Flags“ als Datentabelle (Stammdaten, kein Auswertungsergebnis) |

## Paritätsmatrix

Legende: ✔ vorhanden, ◐ teilweise, – fehlt. „Komponente“ nennt den Baustein in
`@flowaudit/ui`, der die Fähigkeit übernimmt.

| Fähigkeit | riskanalysis | flowinvoice | FlowStat | Komponente |
|---|---|---|---|---|
| Verteilung je Code (Treffer, Anteil) | ◐ nur Zahl | ✔ je Kategorie | ◐ nur Zahl | `RiskFlagSummary` |
| Volumen je Code | – (Backend ✔) | – | – | `RiskFlagSummary` (aus `summary[].volumen`) |
| Unbestimmt je Code mit Begründung und Anzahl | – (Backend ✔) | – | – | `RiskFlagSummary` |
| Übersprungene Regeln („Spalten fehlen“) | – | – | – | `RiskFlagSummary`, Hinweisleiste |
| Tabelle je Datensatz mit Zustand je Code | ◐ nur Treffercodes | ◐ nach Dokument | – | `RiskFlagTable` |
| Filter nach Code | ✔ (Query) | ◐ Unterkategorie | – | `RiskFlagFilter` |
| Filter nach Zustand (Treffer/unbestimmt/ohne) | – | – | – | `RiskFlagFilter` |
| Textsuche im Datensatzschlüssel | – | – | – | `RiskFlagFilter` |
| Karte je Merkmal: Code, Bezeichnung, Begründung | ◐ nur Code | ✔ | – | `RiskFlagCard` |
| Profil und Version, Fingerabdruck, Status am Befund | – | – | – | `RiskFlagCard`, `RiskProfileInfo` |
| Verwendete Eingabefelder mit Werten | – | ◐ Evidenz | – | `RiskFlagCard` (`inputs`) |
| Angewandte Schwellen/Parameter | – | ◐ Score-Tabelle | – | `RiskFlagCard` (`parameters`, `evidence`) |
| Schwere mit Farbe **und** Text | ◐ eine Farbe | ✔ | – | `RiskFlagCard`, `RiskFlagTable` |
| Fundstelle in der Quelle (Repository, Datei, Symbol) | – | – | – | `RiskFlagCard` (aufklappbar) |
| Eingabefelder je Profil (Bedeutung, Pflicht, Folge bei Fehlen) | Doku | – | – | `RiskProfileInfo` |
| Spaltenprüfung vor der Auswertung | – | – | – | `RiskProfileInfo` + `POST …/check-columns` |
| Datensatzübergreifende Befunde (Konzentration) | – | ✔ | ◐ Anteil | `RiskFlagSummary` (Abschnitt Datensatzebene) |
| Legacy-Score/Stufe eines Profils | – | ✔ | – | `RiskFlagCard` (Bewertung je Datensatz, nur Anzeige) |
| Export PDF/Word | – | ✔ | – | bewusst nicht Teil der Komponenten (Anwendungssache) |
| Score-Rad/Gauge | – | ✔ | – | bewusst nicht übernommen: kein profilübergreifender Score |

## Festlegungen für die Komponenten

1. **Unbestimmt ist ein eigener Zustand**, nie „kein Merkmal“: eigenes Symbol
   (Fragezeichen), gestrichelter Rahmen, Text „unbestimmt“ plus Begründung
   (z. B. „Nettobetrag fehlt in der Quelle“). Farbe allein trägt keine Bedeutung.
2. **Übersprungen** (Regel lief nicht, Spalten fehlen) ist von „unbestimmt“
   (Regel lief, Datensatz nicht entscheidbar) getrennt und wird mit Grund angezeigt.
3. **Profilbindung sichtbar:** jede Karte nennt Profil, Version und Status;
   `CANDIDATE_HUMAN_DECISION_REQUIRED` und `LEGACY_CHARACTERIZED` erhalten einen Hinweis.
4. **Kein gemeinsamer Score:** Punkte/Stufen erscheinen nur, wenn das Profil
   selbst eine Bewertung hat, und nur mit Profilangabe.
5. **Framework-freie View-Logik** (`src/risk/view/`): Zustände, Verteilung,
   Filter, Formatierung (deutsches Zahlenformat), Parameterbeschriftung. Vue-SFCs
   bleiben dünn (≤ 250 Zeilen), Tabellen deklarativ (Spaltendefinitionen).
6. **Barrierefreiheit:** Zustände als Text und `aria-label`, Tabellen mit
   `<th scope>`, Filter als beschriftete Formularelemente, Karten mit
   `aria-expanded` für Details, Kontrast ≥ 4,5 : 1 in hellem und dunklem Schema.
7. **Einbettung:** Vue-Komponenten direkt; Web Component `<flowaudit-risk-flags>`
   mit Eigenschaften `evaluation` und `profile` (Objekte) oder `api-base`; die
   React-Hülle setzt diese Eigenschaften und leitet Ereignisse
   (`flag-select`, `filter-change`) als Callbacks weiter.
