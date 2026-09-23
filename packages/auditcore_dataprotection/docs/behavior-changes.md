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
| DP-C11 | Empfehlung Konsultation: Freigabe ohne dokumentierte Konsultation möglich. | Freigabe verlangt die dokumentierte Konsultation (`require_consultation_record=True`). | Framework `release_dsfa`; **HUMAN_DECISION_REQUIRED**, ob die Konsultation vor der DSFA-Freigabe oder erst vor Verarbeitungsbeginn nachzuweisen ist. Abschaltbar nur ausdrücklich. |
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

1. **DP-C11** Zeitpunkt der Konsultation im Freigabeablauf.
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

Neue Profilfassungen `regulierung.dsgvo` und `regulierung.hdsig_ji`
`2026.10.1`, abgeleitet aus `2026.09.1`. Die Fassungen `2026.09.1`, der
`legacy`-Vertrag und alle Replay-Ergebnisse bleiben unverändert.

| ID | Änderung | Grundlage |
|---|---|---|
| DP-E01 | Schwere 4 ergibt mindestens die Stufe `mittel`, auch wenn das Produkt darunter liegt; Vorschlag und Begründung folgen der angehobenen Stufe. | Fachliche Festlegung vom 23.09.2026; EDSA-Explainer Fn. 9; DSK-Kurzpapier Nr. 18, S. 5 |
| DP-E02 | Entscheidung `verworfen`; wird nie vorgeschlagen, verlangt daher eine Begründung; eine sonst nötige Konsultation entfällt. | EDSA-Vorlage Abschnitt 6 |
| DP-E03 | `freigabe_mit_auflagen` verlangt mindestens eine Bedingung; eine inhaltliche Änderung setzt sie mit der Entscheidung zurück. | EDSA-Vorlage Abschnitt 6 |
| DP-E04 | Konsultation mit Grund; im DSGVO-Profil auch Art. 36 Abs. 5 DSGVO. | EDSA-Vorlage Abschnitt 6 |
| DP-E05 | Szenarien mit Risikoquelle, Umständen und Hinnehmbarkeit. | EDSA-Vorlage 3.1, 4.1, 4.2.b |
| DP-E06 | Maßnahmen mit Bereich und Umsetzungsstand; im DSGVO-Profil fünf dokumentierende Maßnahmen ohne rechnerische Minderung. | EDSA-Vorlage 2.3, 4.2.a |
| DP-E07 | Maßnahmenplan (Vorhaben, Verantwortlich, Termin). | EDSA-Vorlage 4.2.c |
| DP-E08 | Stammdaten der Abschätzung; „Beteiligte“ und „Umfang“ sperren die Freigabe, wenn sie fehlen. | EDSA-Vorlage 0.5 |
| DP-E09 | WP 248 wird der Art.-29-Datenschutzgruppe zugeordnet (vom EDSA am 25.05.2018 bestätigt), nicht dem EDSA. | WP 248 rev.01 |

Offen (HUMAN_DECISION_REQUIRED): die Normen des Dritten Teils HDSIG zu den
Maßnahmenbereichen im JI-Profil; ob die förmliche Billigung (Explainer Rn. 10)
Pflichtfeld wird; ob nicht umgesetzte Maßnahmen eine Freigabe ohne Auflagen
sperren statt nur einen Hinweis auszulösen; Übernahme der Endfassung der
EDSA-Vorlage nach der Konsultation.
