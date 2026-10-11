# Spezifikation auditcore_dataprotection

Stand: 08.10.2026, Paketversion 0.6.0 (Prüfkatalog: `docs/pruefkatalog-abgleich.md`). Charakterisierung: 241 Einzelfälle und
65 Ablaufschritte der Quellanwendung regulierung@`a5d48ea`
(`tests/fixtures/regulierung_legacy_observed.json`, Replay in
`tests/test_legacy_replay.py`, Exporte in `tests/test_legacy_exports.py`);
Abweichungen DP-C01 bis DP-C21 und Profilfassungen DP-E01 bis DP-E18 in
`docs/behavior-changes.md`. Eigenschaftstests: `tests/test_spezifikation.py`.

## Zweck

Frameworkunabhängige Bibliothek für Verzeichnisse von Verarbeitungstätigkeiten
(VVT, Art. 30 DSGVO) und Datenschutz-Folgenabschätzungen (DSFA, Art. 35/36
DSGVO bzw. entsprechendes Recht für Justiz und Inneres): Schwellwertanalyse,
Brutto-/Nettorisiko, begründeter Vorschlag, Versionierung, Freigabe im
Vier-Augen-Prinzip und Ausgabe (HTML, XLSX, optional PDF). Regeln stehen in
versionierten, quellengebundenen Profilen; der Vorschlag ist eine Empfehlung,
Entscheidung und Freigabe bleiben zurechenbare menschliche Schritte. Die
Profile sind charakterisiertes Softwareverhalten, keine rechtliche Prüfung.

## Verträge

| Bereich | Funktion/Klasse | Eingabe | Ausgabe | Nebenwirkungen |
|---|---|---|---|---|
| Profile | `available_profiles()`, `load_profile(id, version)` | ausdrückliche Kennung und Version (kein Standardprofil) | `RuleProfile` mit `reference` = {id, version, fingerprint} | liest Paketdaten |
| Schwellwertanalyse | `screen(profile, answers)` | Zuordnung Frage → `True`/`False`, `None`/`"unbekannt"`, `"ja"`/`"nein"`, `Answer` oder `{"ja"/"value", "begruendung"}` | `ScreeningResult`: `pflicht`, `keine_pflicht` oder `unvollstaendig`, Punkte, Begründung, Ablaufspur | keine |
| Risiko | `assess_risk(profile, scenarios)` | Szenarien mit Schutzziel, Beschreibung, Schwere und Wahrscheinlichkeit (Skala des Profils), Maßnahmen, optional begründete Restwerte | Brutto = Schwere × Wahrscheinlichkeit, Netto nach begrenzter Minderung; Stufen nach Produktgrenzen (Schema 1) oder Risikomatrix mit Mindeststufe (Schema 2) | keine |
| Vorschlag | `propose(profile, answers, scenarios=())` | wie oben | `Proposal` mit Empfehlung `nur_schwellwert`, `unvollstaendig`, `freigabe`, `freigabe_mit_auflagen` oder `konsultation_aufsichtsbehoerde`, Prüfhinweisen, Ablaufspur, Profilreferenz | keine, deterministisch |
| Konsultation | `finalize_consultation(profile, proposal, decision)` | vollständiger Vorschlag, Entscheidung aus `DECISIONS` | Vorschlag mit endgültigem Hinweis (ab Profil 2026.10.2) | keine |
| Vorbelegung | `prefill_from_activity(activity)` | Tätigkeit des Verzeichnisses | Vorschläge für Antworten mit Begründung | keine |
| Verzeichnis | `RegisterService(repository, authorizer, audit, clock, ids, profile)`: `save_draft`, `release`, `draft`, `released`, `effective`, `history`, `activity` | Mandant, handelnde Person (`Actor`), Inhalt, erwartete Revision | `RegisterVersion` | über die Ports der Anwendung (Ablage, Rechte, Protokoll, Uhr, Kennungen) |
| Folgenabschätzung | `AssessmentService`: `start`, `update`, `decide`, `record_dpo_request`, `record_dpo_statement`, `release`, `open_points`, `review_required`, `overview` | wie oben | `Assessment` | über die Ports |
| Ausgabe | `export.assessment_report`, `render_assessment_html`, `register_report`, `render_register_html`, XLSX (Extra `excel`, über `auditcore_reporting`), PDF (Extra `pdf`) | Fassungen und Profil | HTML, XLSX-Bytes, PDF-Bytes | keine |
| REST | `auditcore_dataprotection.web` (Extras `web`/`fastapi`) | JSON | JSON; Fehler mit stabilem `code` | über die Ports |
| Arbeitsbereich | `ActivityWorkspace(registers, assessments, authorizer, clock, profile, transfers?, decisions?, assessment_service?)`: `overview`, `evaluate`, `create_activity`, `answer`, `confirm`, `navigate`, `update_item`, `confirm_item`, `set_records` | Mandant, Person, Tätigkeit, erwartete Revision | Übersicht bzw. `RegisterVersion`; `Evaluation` mit `StatusAxes` und Sperren | über `RegisterService.save_draft` (Rechte, Revision, Protokoll) |
| Betriebsentscheidung | `OperationService.decide(tenant, actor, DecisionRequest)` | Ergebnis, Umgebung, Umfang, Begründung, optional Dringlichkeitsfall | `OperationalDecision`, gebunden an Fassung und Inhaltshash | Port `OperationRepository`, Protokoll |
| Zentrale Übernahme | `CentralRegisterService`: `mark_exported`, `transfer`, `confirm_takeover` | freigegebene Fassung | `TransferRecord` | Ports `TransferRepository`, `CentralRegisterPort` |
| Referenzadapter | `memory` (In-Memory-Ablage, Rollen, Protokoll, feste Uhr, fortlaufende Kennungen) | – | für Tests und Beispiele | keine |

## Invarianten

| Nr. | Invariante | Test |
|---|---|---|
| I1 | Offene oder als unbekannt gekennzeichnete Antworten gelten nie als „Nein“: ohne bejahtes Muss-Kriterium und unter der Punktschwelle ist das Ergebnis `unvollstaendig` (Empfehlung `unvollstaendig`); nur eine vollständig verneinte Erhebung ergibt `keine_pflicht`. | `test_i1_offene_angaben_gelten_nie_als_nein` |
| I2 | Die Schwellwertanalyse ist monoton: ein weiteres „Ja“ macht aus einer Pflicht nie etwas anderes. | `test_i2_schwellwertanalyse_monoton_in_ja_antworten` |
| I3 | Ein bejahtes Muss-Kriterium ergibt `pflicht`, gleich wie die übrigen Antworten lauten. | `test_i3_muss_kriterium_entscheidet_allein` |
| I4 | Je Achse gilt Untergrenze ≤ Nettowert ≤ Bruttowert; die Minderung durch Maßnahmen ist je Achse durch die Obergrenze des Profils beschränkt; netto ≤ brutto. | `test_i4_massnahmen_mindern_begrenzt_und_nie_unter_die_untergrenze` |
| I5 | Die Empfehlung folgt dem höchsten Nettorisiko: ein weiteres Szenario senkt sie nie. | `test_i5_zusaetzliches_szenario_senkt_die_empfehlung_nie` |
| I6 | Eingaben werden geprüft, nicht umgedeutet: nicht boolesche Antworten (`"false"`, `0`, `1`), unbekannte Fragen, doppelte Maßnahmen und Werte außerhalb der Skala ergeben `ValidationError`. | `test_i6_eingaben_werden_geprueft_nicht_umgedeutet` |
| I7 | Der Vorschlag ist deterministisch und nennt Profilkennung, Version und Fingerabdruck. | `test_i7_vorschlag_deterministisch_und_profilgebunden` |
| I8 | Ab Profilfassung 2026.10.2 gibt der Vorschlag höchstens einen vorläufigen Konsultationshinweis; endgültig „erforderlich“ ist er genau dann, wenn die vollständige Bewertung die Konsultation empfiehlt und die Verarbeitung nicht verworfen wird. Ein unvollständiger Vorschlag erhält keinen endgültigen Hinweis. | `test_i8_konsultation_nur_bei_hohem_restrisiko_nach_entscheidung` |
| I9 | Vier-Augen-Prinzip: wer einen Entwurf bearbeitet hat (auch in früheren Revisionen), darf ihn nicht freigeben; eine andere berechtigte Person darf es. Freigaben sind mandantengebunden. | `test_i9_vier_augen_wer_bearbeitet_hat_gibt_nicht_frei` |
| I10 | Speichern und Freigeben verlangen die aktuelle Revision (optimistische Sperre); eine veraltete Revision wird abgewiesen, eine gültige erhöht die Revision derselben Fassung. | `test_i10_veraltete_revision_wird_abgewiesen` |

| I11 | Ab Profilfassung 2026.10.4 begründet § 64 Abs. 1 Nr. 2 HDSIG die Konsultation unabhängig vom Restrisiko; nur das Verwerfen der Verarbeitung hebt sie auf. | `test_t14_paragraf_64_nr_2_eigenstaendig_trotz_niedrigem_restrisiko` |
| I12 | „Keine Folgenabschätzung erforderlich“ (2026.10.4) verlangt eine vollständige Schwellwertanalyse und eine eigene Begründung. | `test_t10_keine_dsfa_ohne_eigene_begruendung_abgelehnt`, `test_t10_keine_dsfa_bei_unklarer_vorpruefung_unmoeglich` |
| I13 | „Unklar“ und unbestätigte Vorschläge schreiben keinen Wert in das Verzeichnis; Antworten zu ausgeblendeten Fragen wirken nicht. | `test_wizard_unklar_wird_aufgabe_und_ausgeblendete_antworten_wirken_nicht`, `test_t33_ki_vorschlag_bleibt_unbestaetigt` |
| I14 | Eine positive Betriebsentscheidung ist nur ohne Sperre möglich und gilt nur für die entschiedene Fassung. | `test_t15_kein_allgemeiner_override_waehrend_konsultation`, `test_vollstaendiger_durchlauf_bis_zur_betriebsentscheidung` |
| I15 | Dieselbe Fassung wird höchstens einmal übertragen; „übernommen“ setzt eine zentrale Kennung voraus. | `test_t25_t26_zentrale_uebernahme_idempotent_und_konflikt` |
| I16 | „Nachgewiesen“ setzt einen erreichbaren, geprüften, gültigen Nachweis passender Art voraus; geplante Maßnahmen senken das nachgewiesene Restrisiko nicht. | `test_t21_vvt_historie_ersetzt_keine_fachprotokollierung`, `test_t36_veralteter_nachweis_nicht_gruen`, `test_t12_geplante_massnahme_nicht_als_wirksam` |

## Fehlerfälle

Alle Fehler erben von `DataProtectionError` und tragen einen stabilen `code`,
den die Anwendung auf HTTP- oder Oberflächenantworten abbildet:

| Klasse | `code` | Wann |
|---|---|---|
| `ProfileError` | `profile_error` | unbekanntes Profil, Version, ungültiger Profilinhalt, Schemawechsel 2 → 1 |
| `ValidationError` | `validation_error` | unbekannte Fragen, nicht boolesche Antworten, doppelte Kriterien oder Maßnahmen, Werte außerhalb der Skala, unbekanntes Schutzziel, fehlende Beschreibung, unzulässige Entscheidung, endgültiger Hinweis auf unvollständigem Vorschlag, doppelte Tätigkeitskennungen |
| `AuthorizationError` | `forbidden` | Person fehlt oder hat das Recht nicht |
| `TenantMismatchError` | `tenant_mismatch` | Objekt gehört zu einem anderen Mandanten |
| `NotFoundError` | `not_found` | Fassung nicht vorhanden (auch fremde Mandanten) |
| `ConflictError` | `conflict` | kein offener Entwurf, unvollständiges Verzeichnis bei Pflichtprüfung |
| `StaleRevisionError` | `stale_revision` | erwartete Revision veraltet |
| `LockedVersionError` | `version_locked` | freigegebene Fassung soll geändert werden |
| `FourEyesViolation` | `vier_augen_verletzt` | Bearbeiter, Entscheider oder DSB will freigeben |
| `CentralRegisterUnavailable` | `central_register_unavailable` | zentrales Verzeichnis nicht erreichbar; Stand unverändert, später nachführen |

Blockierende Prüfhinweise (`Issue(blocking=True)`) sind kein Fehler: sie stehen
im Vorschlag und sperren – je nach Profilfassung – Entscheidung bzw. Freigabe
oder werden im Dokumentationsmodus (2026.10.3) als offene Punkte gespeichert.

## Abgrenzung

- Keine Datenbank, keine Sitzung, kein HTTP-Server, keine Benutzerverwaltung:
  Ablage, Rechte, Protokoll, Uhr und Kennungen kommen über Ports der Anwendung.
- Keine rechtliche Bewertung im Einzelfall; Profile bilden Kataloge,
  Schwellen und Texte versioniert ab. Rechtsregime werden nicht vermischt
  (je Regime ein eigenes Profil) und nicht per Schlüsselwort geraten.
- Keine automatische Entscheidung oder Freigabe; der Vorschlag ist eine
  Empfehlung.
- Keine Konsultation der Aufsichtsbehörde selbst; die Bibliothek dokumentiert
  Hinweis und Nachweis.
- Tabellarische XLSX-Ausgabe über `auditcore_reporting`; eigene Stile der
  Legacy-Arbeitsmappen bleiben ein eigener Adapter.

## Bewusste Abweichungen vom Altverhalten

Vollständige Liste mit Begründung: `docs/behavior-changes.md`. Das Modul
`auditcore_dataprotection.legacy` reproduziert die Quellanwendung exakt
(Replay aller Fälle, HTML-Bericht bytegleich); die Profile
`regulierung.dsgvo` und `regulierung.hdsig_ji` in Fassung 2026.09.1 bleiben
unverändert. Beide dienen der verhaltensgleichen Umstellung bestehender
Anwendungen und sind nicht für neue Aufrufer gedacht.

| Altverhalten | Gewolltes Verhalten | Legacy-Variante | Nachweis |
|---|---|---|---|
| Leere oder unvollständige Antworten ergeben `keine_pflicht`/`nur_schwellwert`; leere Fassung wurde freigegeben (DP-C01) | drei Werte ja/nein/unbekannt, Ergebnis `unvollstaendig` | `legacy.legacy_threshold`, `legacy.legacy_proposal` | I1 |
| Unbekannte Frageschlüssel übersprungen, `"false"`/`0`/`1` per `bool()` umgedeutet, doppelte Kriterien doppelt gezählt (DP-C02 bis DP-C04) | `ValidationError` | `legacy.legacy_threshold` | I6 |
| Doppelte Maßnahmen mehrfach angerechnet, unbekannte ignoriert, Restwerte ungeprüft (DP-C05/C06) | `ValidationError`, Restwerte nur in der Skala | `legacy.legacy_risk` | I4, I6 |
| Pflicht ohne Szenario → Konsultationsempfehlung (DP-C08) | `unvollstaendig` mit `risk_assessment_missing` | `legacy.legacy_proposal` | `test_calculation.py` |
| Konsultation schon während der Erhebung als feststehend (DP-C21) | vorläufiger Hinweis, endgültig erst nach der Entscheidung | Profil `regulierung.dsgvo` | I8 |
| Vier-Augen nur gegen den letzten Bearbeiter, DSB konnte freigeben (DP-C13/C14) | alle Bearbeiter, Entscheider und die DSB sind ausgeschlossen | – | I9 |
| Mandant beim Laden nicht geprüft (DP-C12) | jeder Zugriff mandantengebunden | – | I9 |
| Rechtsrahmen per Schlüsselwort vorgeschlagen (DP-C20) | Profil ausdrücklich gewählt | `legacy.legacy_regime_suggestion` | `test_legacy_replay.py` |
| Vorbelegungstext „liegt über dem Anhaltswert“ auch beim Anhaltswert selbst (DP-C19) | „erreicht … oder liegt darüber“ | `legacy.legacy_prefill` | `test_calculation.py` |
| VVT-Arbeitsmappe speichert `=1+1` als Formel (DP-C15) | Texte als Literal | – | `test_exports.py` |
| HTML-Bericht der Quellanwendung | neuer Bericht mit offenen Punkten | `legacy.legacy_report_html` | `test_legacy_exports.py` |

Offene fachliche Entscheidungen (HUMAN_DECISION_REQUIRED) stehen in
`docs/behavior-changes.md` (u. a. Normen der Maßnahmenbereiche im JI-Profil,
Pflichtfeld förmliche Billigung, Zuordnung geteilter Matrixfelder).
