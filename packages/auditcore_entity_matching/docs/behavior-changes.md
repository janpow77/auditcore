# Legacyverhalten und bewusst korrigiertes Verhalten

Quellen: `flowworkshop@a05bb21` und `audit_designer@030a71e`, tatsächlich
ausgeführt (`tools/capture_legacy.py`, 440 Fälle, rapidfuzz 3.10.1). Das Modul
`legacy` reproduziert alle Fälle exakt; der Bibliotheksvertrag weicht nur hier ab:

| ID | Original | Bibliothek | Begründung |
|---|---|---|---|
| EM-C01 | `is_valid_lei` prüft nur das Format; `7LTWFZYICNSX8D621K87` (falsche Prüfziffern) und `00000000000000000000` gelten als gültig. | `check_lei(...).valid` verlangt Format **und** Prüfziffern nach ISO 7064 MOD 97-10 (ISO 17442); `is_lei_format` behält die reine Formatprüfung unter ehrlichem Namen. | Ein LEI-Treffer liefert im Original Konfidenz 100. |
| EM-C02 | `extract_lei_from_text` nimmt das erste formal passende Token. | `extract_lei` überspringt Tokens mit falschen Prüfziffern (`require_checksum=False` stellt das Original her). | wie C01 |
| EM-C03 | Drei Normalisierungen mit unterschiedlichem Ergebnis: state_aid `Müller → mueller`, `SOCIÉTÉ → société`; sanctions/designer `Müller → muller`, `SOCIÉTÉ → societe`. entity_resolution nutzt die state_aid-Variante. | Getrennte Profile `flowworkshop.state_aid`, `flowworkshop.sanctions`, `audit_designer.sanctions`; keine Vereinheitlichung. | Unterschiedliche Vergleichsformen erzeugen unterschiedliche Treffer. |
| EM-C04 | Schwellen (75 Entity Resolution, 70 Designer-Mindestwert, Klassen 97/90/80) als Konstanten im Code. | Nur als benannte Profilwerte; `best_match` verlangt `min_score` ausdrücklich. | Schwellen sind fachliche Einstellungen. |

sanctions (flowworkshop) und `normalisiere_name` (audit_designer) lieferten in
allen 51 Namensfällen identische Ergebnisse und haben identische Tabellen. Sie
bleiben trotzdem zwei Profile, weil sie getrennte Quellen und Consumer haben.

## HUMAN_DECISION_REQUIRED

1. Welche Normalisierung (Umlaut → `ae` oder → `a`) für einen gemeinsamen
   Entitätsbestand maßgeblich ist; heute vergleicht entity_resolution mit der
   state_aid-Variante, das Sanktionsscreening mit der NFKD-Variante.
2. Übernahme der Prüfziffernprüfung (EM-C01) in flowworkshop: bestehende
   Entitäten mit formal passenden, aber ungültigen LEIs würden nicht mehr mit
   Konfidenz 100 zugeordnet.
3. Schwellen, Geburtsdatums-/Länder-Bonus/-Malus und Konfidenzklassen sind nicht
   Teil dieser Bibliothek.
