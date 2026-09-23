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

## Getroffene fachliche Entscheidungen (HUMAN_DECISION, 23.09.2026)

1. **Maßgebliche Normalisierung für einen gemeinsamen Entitätsbestand**, wörtlich:
   „mueller wenn es kein umlaut gibt“. Bleiben Umlaute nicht erhalten, wird
   transliteriert: ä → ae, ö → oe, ü → ue, ß → ss. Das entspricht dem Profil
   `flowworkshop.state_aid`; es ist das **empfohlene Profil für neue Consumer**
   (`load_profile("flowworkshop.state_aid", "2026.09.1")`). Die Profile
   `flowworkshop.sanctions` und `audit_designer.sanctions` (`Müller → muller`)
   bleiben unverändert als Legacy-Profile reproduzierbar; bestehende Funktionen
   werden nicht still umgestellt. Die Bibliothek hat keine profilunabhängige
   Einstiegsfunktion; `normalize` verlangt weiterhin ein ausdrücklich gewähltes
   Profil. Offen bleibt, ob das Sanktionsscreening in flowworkshop und
   audit_designer umgestellt wird: Anfrage und Liste werden dort mit derselben
   Variante normalisiert, eine Umstellung ändert Scores und ist deshalb nicht
   fachlich eindeutig (dokumentiert, nicht umgesetzt).
2. **LEI-Prüfziffernprüfung (EM-C01/EM-C02) wird eingeschaltet.** flowworkshop
   nutzt `check_lei`/`extract_lei`; LEIs mit falschen Prüfziffern, auch `000…0`,
   gelten nicht als gültig und begründen keinen Treffer mit Konfidenz 100
   (flowworkshop-Commit `9fbd950`, Branch `feat/auditcore-entity-matching`).
   Die Legacy-Funktionen `flowworkshop_is_valid_lei` und
   `flowworkshop_extract_lei_from_text` bleiben zur Reproduktion des alten
   Verhaltens erhalten.

## 0.2.0: Profile 2026.09.2 für den umgestellten Sanktionsabgleich

Beide Quellanwendungen haben die Entscheidung 1 für ihr Sanktionsscreening
umgesetzt (audit_designer PR #380, Merge `1254591`; flowworkshop PR #49,
Merge `3d1cb40`). Kein vorhandenes Profil bildet das ab: `flowworkshop.state_aid`
schreibt zwar `ä → ae` um, lässt aber `ø`, `ł`, `É` stehen und hat andere
Rechtsform-/Füllwortlisten. Deshalb neue Profilversionen, bestehende Profile
und Legacy-Funktionen bleiben unverändert (tatsächlich ausgeführt:
`tools/capture_transliteration.py`, 220 Fälle, `tests/fixtures/transliteration_observed.json`):

| Profil | Quelle | Verfahren |
|---|---|---|
| `audit_designer.sanctions` 2026.09.2 | `falte_diakritika`/`normalisiere_name` | neuer Algorithmus `casefold_nfc_fold_nfkd`: Kleinschreibung, **NFC**, Faltungstabelle mit `ä/ö/ü → ae/oe/ue`, `ß → ss`, `ø → o`, `ł → l`, `æ → ae`, `œ → oe` …, danach NFKD ohne Akzente |
| `flowworkshop.sanctions` 2026.09.2 | `UMLAUT_UMSCHRIFT` + `normalize_name` | bisheriger Algorithmus `casefold_fold_nfkd`; die vor der Kleinschreibung angewandte Umschrift ist nach `casefold` gleichwertig als Faltungseintrag abgebildet (alle 110 Namensfälle identisch) |

Einziger beobachteter Unterschied der beiden Varianten: zerlegt geschriebene
Umlaute (`u` + kombinierendes Trema). Der Designer setzt vorher NFC ein
(`Mu\u0308ller → mueller`), flowworkshop nicht (`→ muller`); bei `A\u0308G`
entfällt in flowworkshop dadurch sogar der Token als Rechtsform `ag`.
Legacy-Funktionen: `designer_normalisiere_name_umschrift`,
`flowworkshop_normalize_name_umschrift`.

## HUMAN_DECISION_REQUIRED

1. ~~Umstellung des Sanktionsscreenings auf die Transliteration~~ — in beiden
   Anwendungen am 23.09.2026 umgesetzt (Profile 2026.09.2). Offen bleibt nur,
   ob zerlegt geschriebene Umlaute wie im Designer (NFC) auch in flowworkshop
   umgeschrieben werden sollen.
2. Schwellen, Geburtsdatums-/Länder-Bonus/-Malus und Konfidenzklassen sind nicht
   Teil dieser Bibliothek.
