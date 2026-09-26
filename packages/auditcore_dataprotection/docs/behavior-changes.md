# Legacyverhalten und bewusst korrigiertes Verhalten

Quelle: `janpow77/regulierung@a5d48ea4b90a410210ec25e707781ef9e21ad743`.
Alle Legacy-Beobachtungen stammen aus tatsächlich ausgeführtem Originalcode
(`tools/capture_regulierung_legacy.py`, Fixture
`tests/fixtures/regulierung_legacy_observed.json`: 241 Einzelfälle, 65 Ablauf-
schritte auf einer isolierten In-Memory-SQLite-Datenbank, Exporte).

Zwei Verträge sind getrennt und beide getestet:

* `auditcore_dataprotection.legacy` reproduziert das Original exakt
  (Replay aller 241 Fälle, HTML-Bericht bytegleich, Workbooks zellgleich bis
  auf DP-C15). Er dient der verhaltensgleichen Umstellung bestehender Consumer.
* `calculation`, `register` und `assessment` bilden den korrigierten
  Bibliotheksvertrag. Jede Abweichung ist unten begründet und in den Tests
  jeweils zusammen mit dem Legacy-Ergebnis geprüft.

| ID | Beobachtung im Original | Korrigierter Vertrag | Begründung |
|---|---|---|---|
| DP-C01 | Leere oder unvollständige Antworten ergeben `keine_pflicht`/`nur_schwellwert`; eine Fassung ohne jede Antwort wurde im Ablauf tatsächlich freigegeben (`dsfa-empty-release`). | Drei Werte ja/nein/unbekannt; Ergebnis `unvollstaendig`, Entscheidung und Freigabe gesperrt. | Fehlende Angaben dürfen nicht unbemerkt zu Nein oder Freigabe werden (Auftrag; Framework `docs/dsfa-werkzeug.md`). |
| DP-C02 | Unbekannte Frageschlüssel werden übersprungen. | `ValidationError`. | Katalogversion und Eingabe müssen zusammenpassen. |
| DP-C03 | `"false"`, `0`, `1` werden per `bool()` umgedeutet (`"false"` = ja). | Nur echte Booleans bzw. ausdrücklich unbekannt. | Framework: „kein anderer Typ, keine stille Null“. |
| DP-C04 | Dieselbe Punktfrage doppelt zählt zwei Punkte und löst die Pflicht aus. | Doppelte Kriterien sind ein Fehler (`parse_answer_list`); die Zuordnungsform schließt sie aus. | Eindeutige Antworten. |
| DP-C05 | Doppelte Maßnahmen werden mehrfach angerechnet, unbekannte ignoriert. | Beides `ValidationError`; jede Maßnahme wirkt einmal. | Nachvollziehbare Maßnahmenwirkung. |
| DP-C06 | Restwerte werden nicht geprüft; `0/0` ergab Stufe `offen` und Empfehlung `freigabe`, `9/0` wurde gespeichert. | Restwerte nur 1..4. | Wertebereich der Skala; sicherheitsrelevant. |
| DP-C07 | Ein ausdrücklich gesetzter Restwert braucht keine Begründung. | Blockierender Hinweis `residual_without_justification` (sperrt Freigabe, nicht Berechnung). | Der Quellbericht verlangt selbst die Begründung der Fachabteilung. |
| DP-C08 | Pflicht ohne Szenario ergibt Empfehlungsschlüssel `konsultation_aufsichtsbehoerde`. | `unvollstaendig` mit `risk_assessment_missing`; Text unverändert. | Ohne Risikobetrachtung liegt kein Konsultationsergebnis vor. |
| DP-C09 | Beliebige Entscheidungswerte (`irgendwas`) werden mit Begründung angenommen. | Nur die vier Empfehlungswerte. | Eindeutige, auswertbare Entscheidung. |
| DP-C10 | Nach DSB-Votum und Entscheidung geänderte Antworten behalten Votum und Entscheidung. | Inhaltliche Änderung entfernt Entscheidung, Stellungnahme, Folgerung und Konsultation; Status zurück auf `entwurf`; Audit-Ereignis `review_reset`. | Votum und Entscheidung bezogen sich auf anderen Inhalt (erneuter Prüfbedarf). |
| DP-C11 | Empfehlung Konsultation: Freigabe ohne dokumentierte Konsultation möglich. | Freigabe verlangt die dokumentierte Konsultation (`require_consultation_record=True`). | Framework `release_dsfa`. Zeitpunkt **DECIDED** am 23.09.2026 (Nutzerentscheidung A5, siehe DP-C21): Der Hinweis entsteht mit der abschließenden Bewertung; der Nachweis ist vor der Freigabe zu führen. Abschaltbar nur ausdrücklich. |
| DP-C12 | `verwaltung.lade(dsfa_id)` und die API-Routen prüfen den Mandanten der Fassung nicht (`dsfa-foreign-tenant-load`). | Jeder Zugriff ist mandantengebunden; Fremdobjekte verhalten sich wie nicht vorhanden. | Mandantentrennung (F-01). Consumer-Fix separat. |
| DP-C13 | Vier-Augen vergleicht nur mit dem letzten Bearbeiter; frühere Bearbeiter dürfen freigeben. | Freigebende Person darf die Fassung nicht bearbeitet oder entschieden haben. | Framework: Ersteller und Freigeber verschieden. |
| DP-C14 | DSB-Stellungnahme ist keiner Person zugeordnet; die oder der DSB könnte freigeben. | Stellungnahme mit Person; diese darf nicht freigeben. | Quellkommentar zu Art. 38 Abs. 3 und 6 DSGVO, im Original nicht erzwungen. |
| DP-C15 | VVT-Workbook speichert `=1+1` als Formel. | Alle Texte werden als Literal geschrieben. | Formel-Injektion in Exporten (F-04). |
| DP-C16 | Änderungserkennung `(alt or "") != (neu or "")` übersieht `False`/`0` → leer. | Nur `None`, `""` und fehlend gelten als gleich. | Wechsel auf „nicht angegeben“ ist wesentlich. |
| DP-C17 | Register-Freigabe ohne Inhaltsprüfung. | Freigabe verlangt Pflichtangaben nach Art. 30 Abs. 1 (`require_complete_release`). | Auftrag „erforderliche Beschreibungen, Prüfungen“. |
| DP-C18 | Doppelte Tätigkeitskennungen werden unverändert übernommen. | `ValidationError`. | Stabile, eindeutige Kennungen (ADR-002 des Frameworks). |
| DP-C19 | Vorbelegungstext „liegt damit über dem Anhaltswert“ auch bei genau 10000; `n`-Formatierung ohne Tausenderpunkt; `True`/`"1e4"` als Zahl. | Text „erreicht … oder liegt darüber“, Tausenderpunkt; nur ganze Zahlen. | Text entsprach nicht der Rechenregel `>=`. |
| DP-C20 | Rechtsrahmen wird per Schlüsselwortheuristik (KPAnG/Bußgeld) vorgeschlagen. | Kein automatischer Vorschlag; Profil wird ausdrücklich gewählt. | Anwendungsspezifisch; Regime nicht still vereinheitlichen. Heuristik bleibt in `legacy`. |

Unverändert übernommen sind insbesondere Frage- und Maßnahmentexte, Fundstellen,
Punktschwelle 2, Stufen bis 4/9/ab 10, Minderungsobergrenze zwei Stufen je Achse
mit Untergrenze 1, Empfehlungsschwellen 5/10, Mindestbegründung 50 Zeichen,
Statusnamen sowie die Reihenfolge der Freigabeprüfungen und deren Meldungstexte.

## Offene fachliche Entscheidungen (HUMAN_DECISION_REQUIRED)

1. ~~**DP-C11** Zeitpunkt der Konsultation im Freigabeablauf.~~ **DECIDED**
   am 23.09.2026, siehe DP-C21.
2. **JI-Profil:** Das Original wendet im Dritten Teil HDSIG die harten Kriterien
   der DSGVO als „strengeren Maßstab“ an. Das ist als Quellprofil
   `regulierung.hdsig_ji` versioniert, nicht als allgemeine Rechtsauslegung.
3. **Framework-Variante:** `verwaltung-app-framework/framework/core/dsfa.py`
   hat abweichende Schlüssel, eine leere Muss-Liste, Mindestbegründung 30,
   dreistufige Restrisiken und andere Voten. Sie wurde nicht mit dem
   regulierung-Profil zusammengeführt.
4. Übernahme des korrigierten Ablaufs (statt `legacy`) in `regulierung` selbst:
   verändert Ergebnisse bestehender Fassungen (C01, C06, C08) und ist dort
   fachlich freizugeben.

## Wiederverwendung vorhandener Renderer

`render_register_xlsx` und `render_overview_xlsx` erzeugen flache Tabellen und
verwenden dafür `auditcore_reporting.render_workbook` (Profil `plain-v1`,
formelsicher, begrenzt). Die Legacy-Arbeitsmappen der Quellanwendung benötigen
verbundene Zellen, Abschnittsüberschriften je Referat und eigene Stile; dieser
Vertrag wird von `ReportTable` nicht abgedeckt. Sie bleiben deshalb ein eigener
openpyxl-Adapter mit derselben Formelsicherheit (DP-C15). Der HTML-Bericht ist
reine Standardbibliothek; PDF bleibt ein optionaler WeasyPrint-Adapter wie im
Original. Geprüft mit openpyxl 3.1.5 und 3.0.10 (Debian Bookworm).

## Profilfassung 2026.10.1 (Schema 2, EDSA-Vorlage 2026 v1.0)

Neue, neutrale Bibliotheksprofile `auditcore.dsgvo` und `auditcore.hdsig_ji`
`2026.10.1`, abgeleitet aus `regulierung.*` `2026.09.1`. Anwendungsbezogene
Textbausteine der Ursprungsanwendung (Standpunkt über Wirtschaftsverbände,
Anhörung nach § 55 OWiG, Beispiele zum KPAnG) sind entfernt; der Standpunkt
der Betroffenen hat den neutralen Baustein „Eingeholt“. Die Profile
`regulierung.*` `2026.09.1`, der `legacy`-Vertrag und alle Replay-Ergebnisse
bleiben unverändert.

| ID | Änderung | Grundlage |
|---|---|---|
| DP-E01 | Die Risikostufe jedes Szenarios ergibt sich Feld für Feld aus der Matrix des DSK-Kurzpapiers Nr. 18 (S. 5), nicht aus den Produktgrenzen 4/9; der Vorschlag folgt der höchsten Stufe nach Maßnahmen (gering → Freigabe, mittel → mit Auflagen, hoch → Konsultation). Abweichend von 2026.09.1: 4×2 und 3×3 hoch, 3×1, 2×1, 2×2, 1×3 und 1×4 mittel. Geteilte Felder nach überwiegendem Flächenanteil: 4×2 (63 % hoch), 3×3 (59 % hoch), 2×1 (53 % Risiko), 1×2 (56 % gering). | Fachliche Festlegung vom 23.09.2026; KP 18, S. 5 |
| DP-E10 | Ab Schwere 4 vor Maßnahmen gilt mindestens `mittel`; Maßnahmen heben das nicht auf, nur ein ausdrücklich begründeter Rest-Schweregrad. Mit der Matrix wirkt die Regel derzeit als Absicherung, weil Schwere 2 bereits überall `mittel` ergibt. | Fachliche Festlegung vom 23.09.2026; EDSA-Explainer Fn. 9 |
| DP-E02 | Entscheidung `verworfen`; wird nie vorgeschlagen, verlangt daher eine Begründung; eine sonst nötige Konsultation entfällt. | EDSA-Vorlage Abschnitt 6 |
| DP-E03 | `freigabe_mit_auflagen` verlangt mindestens eine Bedingung; eine inhaltliche Änderung setzt sie mit der Entscheidung zurück. | EDSA-Vorlage Abschnitt 6 |
| DP-E04 | Konsultation mit Grund; im DSGVO-Profil auch Art. 36 Abs. 5 DSGVO. | EDSA-Vorlage Abschnitt 6 |
| DP-E05 | Szenarien mit Risikoquelle, Umständen und getrennter Hinnehmbarkeit vor Maßnahmen und des Restrisikos. | EDSA-Vorlage 3.1, 4.1.a, 4.1.c, 4.2.b |
| DP-E06 | Maßnahmen mit Bereich und Umsetzungsstand; im DSGVO-Profil fünf dokumentierende Maßnahmen ohne rechnerische Minderung. | EDSA-Vorlage 2.3, 4.2.a |
| DP-E07 | Maßnahmenplan (Vorhaben, Verantwortlich, Termin). | EDSA-Vorlage 4.2.c |
| DP-E08 | Stammdaten der Abschätzung; „Beteiligte“ und „Umfang“ sperren die Freigabe, wenn sie fehlen. | EDSA-Vorlage 0.5 |
| DP-E09 | WP 248 wird der Art.-29-Datenschutzgruppe zugeordnet (vom EDSA am 25.05.2018 bestätigt), nicht dem EDSA. | WP 248 rev.01 |
| DP-E11 | Änderungen nur an Umsetzungsstand oder Maßnahmenplan lassen Entscheidung, Votum und Bedingungen bestehen; Stammdaten, Antworten und Szenarien setzen sie weiter zurück. | Fachliche Festlegung vom 23.09.2026 |
| DP-E12 | Eine Abschätzung nach Schema 2 kann nicht auf ein Profil nach Schema 1 wechseln (Bearbeitung oder Neubewertung); bei einer Neubewertung werden Stammdaten, Umsetzungsstand und Plan gegen das neue Profil geprüft. | Kein stiller Datenverlust |
| DP-E14 | Die Muss-Liste nach Art. 35 Abs. 4 DSGVO (DSK, Version 1.1 vom 17.10.2018) ist vollständig abgebildet: 17 harte Fragen, je Nummer eine, eng am Wortlaut; bisher fassten 5 Fragen 8 Nummern zusammen und formulierten Nr. 1, 4, 5 und 10 enger als die Liste. Nr. 1 und 2 setzen wie die Liste ein weiteres WP-248-Kriterium voraus. Die Schwellwertanalyse hat damit 30 statt 18 Fragen. | Art. 35 Abs. 4 DSGVO; DSK-Liste 1.1 |
| DP-E13 | „verworfen“: keine Konsultationszeile im Bericht; folgt die Entscheidung einer ablehnenden Stellungnahme, entfallen Abweichungsbegründung und Leitungsvorlage. Konsultationsgrund „hohes Restrisiko“ nur, wenn die Bewertung eine Konsultation verlangt. | Art. 36 Abs. 1; WP 243 Ziff. 4.2 |

Offen (HUMAN_DECISION_REQUIRED): die Normen des Dritten Teils HDSIG zu den
Maßnahmenbereichen im JI-Profil (bewusst nicht geraten); ob die förmliche
Billigung und ihr Datum (Explainer Rn. 10) Pflichtfelder werden; die
Zuordnung der vier geteilten Matrixfelder; ob nicht umgesetzte Maßnahmen eine Freigabe ohne Auflagen
sperren statt nur einen Hinweis auszulösen; Übernahme der Endfassung der
EDSA-Vorlage nach der Konsultation.

## Profilfassung 2026.10.2: Zeitpunkt des Konsultationshinweises (DP-C21)

Profile `auditcore.dsgvo` und `auditcore.hdsig_ji` in Fassung `2026.10.2`,
abgeleitet aus `2026.10.1` desselben Profils.

**Status: DECIDED.** Nutzerentscheidung A5 vom 23.09.2026 („alle
empfehlungen“; bis dahin HUMAN_DECISION_REQUIRED zu DP-C11, „weis nicht den
zeitpunkt“): *Der Konsultationshinweis nach Art. 36 Abs. 1 DSGVO wird erst
nach der abschließenden Bewertung gegeben, und nur wenn das Restrisiko
(Nettorisiko nach Maßnahmen) weiterhin hoch ist.*

Rechtsgrundlage: Art. 36 Abs. 1 DSGVO (Konsultation vor der Verarbeitung,
wenn die Folgenabschätzung ein hohes Risiko ergibt, sofern der Verantwortliche
keine Maßnahmen zur Eindämmung trifft) und Erwägungsgrund 94 DSGVO
(Konsultation, wenn sich das Risiko nicht durch geeignete Maßnahmen eindämmen
lässt). Im JI-Profil § 64 HDSIG (Art. 28 Abs. 1 Richtlinie (EU) 2016/680).
Die Profile zitieren das im neuen Abschnitt `recommendation.consultation_notice`.

| ID | Bisher (`regulierung.*` 2026.09.1, `auditcore.*` 2026.10.1, `legacy`) | Ab Profilfassung 2026.10.2 | Begründung |
|---|---|---|---|
| DP-C21 | Sobald das Nettorisiko die Konsultationsstufe erreicht, setzt jeder Vorschlag `consultation_required=True` und nennt die Konsultation als feststehend – auch während der Erhebung. | Der Vorschlag setzt nie `consultation_required`. Er trägt `consultation_notice` mit `final=false` und höchstens dem Status `voraussichtlich_erforderlich` samt gekennzeichnetem Text „Vorläufiger Hinweis: …“. Endgültig wird der Hinweis mit der abschließenden Bewertung (`decide`): Status `erforderlich` nur bei weiterhin hohem Nettorisiko, sonst `nicht_erforderlich`; bei `verworfen` entfällt die Konsultation. | Nutzerentscheidung A5; Art. 36 Abs. 1 DSGVO, ErwG 94 DSGVO. |

Einzelheiten:

* **Abschließende Bewertung** ist die Entscheidung über den Vorschlag auf einer
  vollständigen Erhebung. Mit einem Profil nach 2026.10.2 lehnt `decide`
  Fassungen mit blockierenden Prüfhinweisen ab (offene oder unbekannte
  Antworten, unbegründete Restwerte). Eine unvollständige Bewertung erhält daher
  nie einen endgültigen Hinweis; `finalize_consultation` weist einen
  unvollständigen Vorschlag mit `ValidationError` zurück.
* Hohes Bruttorisiko, das die Maßnahmen unter die Stufe `hoch` der
  Risikomatrix senken (etwa auf `mittel`; die Mindeststufe ab Schwere 4 hebt nur bis `mittel`), ergibt
  keinen Hinweis und nach der Entscheidung `nicht_erforderlich`.
* Eine inhaltliche Änderung nimmt mit der Entscheidung auch den endgültigen
  Hinweis zurück (DP-C10); bis zur neuen Entscheidung gilt wieder der
  vorläufige Hinweis. Speichern ohne inhaltliche Änderung behält ihn.
* Die Freigabe verlangt weiterhin die dokumentierte Konsultation, wenn der
  endgültige Hinweis `erforderlich` lautet oder die Entscheidung auf
  Konsultation lautet (DP-C11).
* Bericht: vorläufiger Hinweis als „Hinweis zur Konsultation (vorläufig)“;
  endgültig erforderlich und nicht dokumentiert wie bisher als blockierende Zeile.
* Keine stille Änderung: `regulierung.*` 2026.09.1, `auditcore.*` 2026.10.1 und `legacy` enthalten den
  Abschnitt nicht und verhalten sich exakt wie zuvor (Replay unverändert, ihre
  Vorschläge enthalten keinen Schlüssel `consultation_notice`). Das Profil
  2026.10.2 unterscheidet sich von 2026.10.1 nur durch diesen Abschnitt und die
  Kennung (Test `test_profile_differs_from_2026_10_1_only_by_notice_and_identity`).

## Profilfassung 2026.10.3: Dokumentationsmodus

Fachliche Festlegung vom 24.09.2026: Die Bibliothek dient der Dokumentation.
In `auditcore.dsgvo` und `auditcore.hdsig_ji` 2026.10.3
(`workflow.release_mode: dokumentation`) verhindert keine inhaltliche Prüfung
mehr die Freigabe. Die Fassungen bis 2026.10.2 und `regulierung.*` sperren
unverändert.

| ID | Änderung |
|---|---|
| DP-E15 | `release_blockers` ist im Dokumentationsmodus leer. `open_points` liefert alle offenen Prüfungen und Hinweise; `release` speichert sie als `release_open_points`, der Bericht zeigt sie unter „Bei der Freigabe offen“. |
| DP-E16 | Für die DSB genügt die dokumentierte Einholung: `record_dpo_request` (bei wem, Datum, erfasst von). Fehlt sie oder fehlt die Stellungnahme, steht das als offener Punkt im Bericht. Eine inhaltliche Änderung setzt die Einholung wie die Stellungnahme zurück. |
| DP-E17 | `decide` ist auch bei unvollständiger Erhebung möglich; fehlende Abweichungsbegründung und fehlende Bedingungen werden offene Punkte. Die Konsultationshinweise werden erst bei vollständiger Bewertung endgültig. |
| DP-E18 | Unverändert sperren Rechteprüfung, Mandantenbindung, Revision, Vier-Augen-Prinzip und dass die DSB nicht selbst freigibt; Eingaben werden weiterhin auf Form und Typ geprüft. |
