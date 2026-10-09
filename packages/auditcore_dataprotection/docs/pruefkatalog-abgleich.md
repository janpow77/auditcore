# Abgleich mit dem Prüfkatalog VVT/DSFA

Stand: 08.10.2026, Paketversion 0.6.0, Profile `auditcore.dsgvo` und `auditcore.hdsig_ji` 2026.10.4,
Fragenkatalog `wizard-2026.10.2`, Checkliste `checklist-2026.10.1`.

Grundlage ist der Prüfkatalog für eine Python-Bibliothek zu VVT und DSFA. Er ist eine
Arbeitsgrundlage und weder eine Codeprüfung noch eine Freigabe. Die Befunde unten betreffen nur
die Software. Rechtliche Inhalte (Normenkette, Profiltexte, Fallgruppen) prüfen die zuständigen
Fachpersonen. Die Bibliothek unterstützt Entscheidungen, übernimmt aber keine rechtliche
Verantwortung.

Befunde: **erfüllt**, **teilweise**, **nicht erfüllt**, **nicht anwendbar – begründet**,
**organisatorisch** (durch Software allein nicht lösbar). Nachweise sind Testnamen; die
Abnahmetests liegen in `tests/test_pruefkatalog_*.py`, die Oberflächentests in
`packages-js/ui-core/test/dataprotection/assistant.spec.ts`, den Paritätsfällen
`cases-datenschutz-assistent.ts` und `packages-js/ui/e2e/dataprotection.api-e2e.ts`.

## Bausteine

| Modul | Aufgabe |
|---|---|
| `register_regime` | Rechtsregime und Rolle je Tätigkeit, § 65 HDSIG (Profiling, Übermittlungen), Verzeichnis des Auftragsverarbeiters, „wenn möglich“-Felder |
| `wizard_catalog`, `wizard` | Fragenkatalog W01 bis W12 als Daten, geführter oder freier Modus, „unklar“ als Aufgabe, Herkunft der Antworten, ausgeblendete Antworten |
| `workspace`, `workspace_assessment` | Ein Dienst für Wizard, Checkliste, Nachweise und Schutzmaßnahmen auf der versionierten Verzeichnisfassung; W09/W10 schreiben direkt in die DSFA |
| `checklist` | CHK-01 bis CHK-30 mit Statusmodell, Nachweisarten und Bestätigung durch eine zweite Person |
| `evidence` | Nachweise (Art, Version, Prüfung, Gültigkeit, Erreichbarkeit), Schutzmaßnahmen, nachgewiesenes Restrisiko |
| `status`, `gates`, `evaluation` | Sechs getrennte Statusachsen, GATE-01 bis GATE-08, eine Auswertung für alle Oberflächen |
| `operation_model`, `operation` | Versionsgebundene Betriebsentscheidung mit eigener Berechtigung, Dringlichkeitsfall § 64 Abs. 4 HDSIG |
| `central_register` | Exportiert, übertragen, übernommen, Konflikt; idempotent; Ausfall ohne Folgen für den Betrieb |
| `publication`, `review_package` | Exportprofile, öffentliches Muster ohne Inhalte, Veröffentlichung nur mit Freigabe, Prüfpaket |
| `change_impact`, `scope` | Erneute Prüfung nach relevanten Änderungen, Personenbezug im Testbetrieb, Dubletten, Anwendungen |
| `web.workspace_api` | REST-Endpunkte (`docs/ui/dataprotection-rest.md`) |
| `@auditcore/ui-core`, `@auditcore/ui`, `@auditcore/ui-react` | `createAssistantController`, `<flowaudit-datenschutz-assistent>` / `FaDatenschutzAssistent`, `FlowauditDatenschutzAssistent` |

## Abschnitt 4: Rechtsprofile und Verzeichnisfelder

| Anforderung | Befund | Umsetzung, Nachweis |
|---|---|---|
| 4.1 Profile `DSGVO`, `HDSIG_TEIL_3`, `UNKLAR` je Tätigkeit | erfüllt | `rechtsregime` je Tätigkeit; `unklar` sperrt; kein stiller Standard (T-01, T-02) |
| 4.1 Verantwortlicher / Auftragsverarbeiter / gemeinsam Verantwortliche | erfüllt | `rolle`; gemeinsam Verantwortliche wie bisher über `gemeinsame_verantwortliche` (T-06) |
| 4.2 Feldabgleich Art. 30 Abs. 1 DSGVO / § 65 Abs. 1 HDSIG | erfüllt | Profiling und Rechtsgrundlage je Übermittlung im HDSIG-Profil sperrend, im DSGVO-Profil als Produktanforderung (T-04, T-05) |
| 4.2 „Wenn möglich“ kein Freibrief | erfüllt | konkrete Angabe oder Begründung und Prüfstelle; sonst sperrend (`test_wenn_moeglich_felder_brauchen_begruendung_und_pruefstelle`) |
| 4.3 Eigene Vorlage Auftragsverarbeiter | erfüllt | `processor_columns`, `check_processor` (T-06) |

## Abschnitt 5: Bibliothek (LIB)

| ID | Befund | Umsetzung, Nachweis, Grenze |
|---|---|---|
| LIB-01 | teilweise | Tätigkeit, Verzeichnisfassung, DSFA (mit Vorprüfung), Konsultation und Betriebsentscheidung sind getrennte Objekte. Anwendungen und Betriebsumgebungen sind Angaben der Tätigkeit (`anwendungs_ids`, `umgebung`), keine eigenen Objekte mit Lebenszyklus. |
| LIB-02 | teilweise | Mehrfachzuordnung über `anwendungs_ids` (T-03). Eine gemeinsame DSFA für mehrere Tätigkeiten ist nicht abgebildet; der Wizard fragt den Bezug ab (W09-11). |
| LIB-03 | erfüllt | Pflichtfelder und Regeln je Profil und Rolle (T-06) |
| LIB-04 | erfüllt | ja/nein/unklar, nicht beantwortet und nicht anwendbar sind verschieden (I1, T-07) |
| LIB-05 | teilweise | Im Assistenten tragen Antworten Herkunft, Person und Zeit; Vorlagen, Importe und KI-Vorschläge wirken erst nach Bestätigung (T-33). Die freie Bearbeitung des Verzeichnisses gilt als bestätigte Eingabe der bearbeitenden Person. |
| LIB-06 | teilweise | Übermittlung, Empfänger und Rechtsgrundlage sind verknüpft; Maßnahmen sind mit Risikoszenarien und Nachweisen verknüpft. Zwecke, Datenkategorien und Fristen bleiben Texte je Tätigkeit. |
| LIB-07 | erfüllt | Syntax (`normalize_content`), Vollständigkeit (`check_activity`), Widersprüche (`personal_data_findings`, Regimeabweichung), Entscheidung (`decide`) getrennt |
| LIB-08 | teilweise | Profile mit Kennung, Version, Fingerabdruck, Quellen und Fundstellen je Frage. Eine fachliche Pflegeverantwortung je Regel ist nicht hinterlegt. |
| LIB-09 | teilweise | Quellen mit Herausgeber und Status; die Sperrregeln sind als Produktvorschlag gekennzeichnet. Eine durchgängige Kennzeichnung Gesetz / Aufsicht / Hausvorgabe je Regel fehlt. |
| LIB-10 | erfüllt | eigene Begründung für „keine DSFA“ (DP-E21, T-10) |
| LIB-11 | erfüllt | Schwellwertanalyse, DSFA und Konsultation getrennt; eigener Tatbestand § 64 Abs. 1 Nr. 2 HDSIG (T-14) |
| LIB-12 | erfüllt | Unklare oder unvollständige Angaben erzeugen keinen positiven Status (T-07, T-10, T-11) |
| LIB-13 | erfüllt | deterministisch, profilgebunden; kein Sprachmodell (I7, T-23) |
| LIB-14 | erfüllt | Abweichung vom Vorschlag mit Begründung; „nicht anwendbar“ mit Begründung und zweiter Person; Sperren lassen sich nicht übersteuern (T-15) |
| LIB-15 | erfüllt | Profil-, Katalog-, Paket- und Verzeichnisversionen getrennt |
| LIB-16 | erfüllt | alte Profile bleiben ausgeliefert, Bewertungen nennen Fingerabdruck (T-23) |
| LIB-17 | teilweise | Neubewertungsbedarf über `change_impact`, `review_required` und GATE-07 (T-24, T-28). Benachrichtigungen versendet die Bibliothek nicht; die Oberfläche meldet Änderungen über das Ereignis `change`. |
| LIB-18 | erfüllt | Idempotenzschlüssel aus Verzeichnis, Fassung und Inhaltshash (T-25); Dublettenhinweise |
| LIB-19 | erfüllt | eigene Zustände, Übernahme nur mit zentraler Kennung (T-25, T-26) |
| LIB-20 | teilweise | Berichte entstehen aus der gespeicherten Fassung ohne laufenden Dienst (T-35); das Archivierungskonzept ist organisatorisch. |
| LIB-21 | organisatorisch | Die Bibliothek hängt an keinem persönlichen Konto; Zuständigkeiten und Vertretung werden erfragt (W03-02, W12-06). |
| LIB-22 | erfüllt | keine Netzaufrufe im Kern; zentrales Verzeichnis nur über einen konfigurierten Port (T-30) |
| LIB-23 | erfüllt | eine Auswertung für Bibliothek, REST und Oberfläche (`test_pruefkatalog_web.py`) |
| LIB-24 | teilweise | Rollen- und Mandantenrechte serverseitig; Betriebsentscheidung braucht `operation.decide`, die Administration erhält sie nicht automatisch (T-17, T-18). Rechte je einzelnem Objekt innerhalb eines Mandanten setzt die Anwendung über ihren `Authorizer` um. |
| LIB-25 | erfüllt | nur JSON-Daten, Typprüfung, keine Ausführung (T-29) |
| LIB-26 | erfüllt | Die Bibliothek protokolliert keine Formulareingaben; Auditereignisse enthalten Kennungen und Status. |
| LIB-27 | erfüllt | Revisionen bei Verzeichnis und DSFA (I10, T-27) |
| LIB-28 | außerhalb dieser Änderung | Repository-Prozess: Code-Gates, Hash-gebundene Releases |
| LIB-29 | nicht geprüft | SBOM und überprüfbare Builds sind nicht Teil dieser Änderung |
| LIB-30 | erfüllt | Sperren betreffen nur positive Schritte; ein Ausfall des Verzeichnisdienstes schaltet nichts ab (T-34) |

## Abschnitt 6: Oberfläche (GUI)

| ID | Befund | Umsetzung, Grenze |
|---|---|---|
| GUI-01 | erfüllt | Jede Frage hat Hinweise als Aufzählung und, wo einschlägig, eine Fundstelle (Katalog 2026.10.2, Test `test_katalog_ist_ein_nummerierter_baum_mit_fundstellen`). Die Fundstellen sind vor der Freigabe gegen die amtlichen Fassungen zu prüfen. |
| GUI-02 | erfüllt | keine Vorbelegung kritischer Fragen |
| GUI-03 | erfüllt | bedingte Fragen; Antworten zu ausgeblendeten Fragen wirken nicht mehr und werden angezeigt |
| GUI-04 | erfüllt | „Unklar“ wird Aufgabe |
| GUI-05 | erfüllt | Reiter „Status und Sperren“ mit sechs Achsen, ohne Gesamturteil |
| GUI-06 | teilweise | Nachweise über Kennungen mit Art, Version und Prüfung; eine Ablage geschützter Dokumente bietet die Bibliothek nicht. |
| GUI-07 | teilweise | Rechte serverseitig, DSB-Stellungnahmen sind geschützt; die Aufgabenliste filtert noch nicht nach Rolle (`filter_items` steht im Kern bereit). |
| GUI-08 | erfüllt | Fehlerübersicht mit Sprung zur Frage, Eingabe bleibt erhalten |
| GUI-09 | teilweise | Speicherstand als Live-Meldung, Konflikterkennung über Revision; lokale Entwürfe überstehen kein Neuladen der Seite. |
| GUI-10 | teilweise | Tastaturbedienung, sichtbarer Fokus, Labels, Status als Text; axe ohne Befund im Browsertest. Eine vollständige BITV-Prüfung steht aus. |
| GUI-11 | nicht anwendbar – begründet | Sitzungen verwaltet die Anwendung; die Komponente legt keine Inhalte in URLs oder Browserablagen ab. |
| GUI-12 | erfüllt | keine Tracker; Ausgabe über Vue/React-Escaping |
| GUI-13 | nicht anwendbar – begründet | keine Dateianhänge in der Bibliothek, nur Verweise |
| GUI-14 | erfüllt | geänderte Angaben öffnen abhängige Prüfpunkte erneut (T-24) |
| GUI-15 | teilweise | öffentliches Muster nur über eigenen Endpunkt mit eigener Berechtigung; eine Vorschau in der Oberfläche fehlt. |
| GUI-16 | erfüllt | Vorschläge gekennzeichnet, Übernahme nur ausdrücklich |
| GUI-17 | teilweise | Filter im Kern; Versionsvergleich und Suche in der Oberfläche fehlen. |
| GUI-18 | teilweise | Sperren nennen Grund, Rolle und nächsten Schritt; Verzeichnisbefunde nennen die Fundstelle. Die Regelkennung je Befund wird nicht überall angezeigt. |

## Abschnitte 7 bis 9: Wizard, Checkliste, Rollen und Sperren

| Anforderung | Befund | Umsetzung |
|---|---|---|
| 7 Wizard W01 bis W12 | erfüllt | Fragenkatalog als nummerierter Entscheidungsbaum nach dem Muster des Checklistendesigners (JA-/NEIN-Zweige, Hinweise, Fundstellen; erzeugt mit `tools/build_wizard_catalog.py`). Übermittlungen werden als Tabelle mit Rechtsgrundlage, die Zahl der Betroffenen als Zahl erfasst; eine Tätigkeit lässt sich allein über den Assistenten vollständig erfassen (`test_taetigkeit_allein_ueber_den_assistenten_vollstaendig`); W09 enthält die Fragen des gewählten Profils; W10 erscheint bei DSFA-Pflicht; Entscheidungen (W09-12, W11-01, W12-05) laufen über DSFA-Entscheidung, Konsultation und Betriebsentscheidung. Wahlweise geführt oder frei (`test_wizard_fuehrt_schrittweise_und_frei_wahlweise`). |
| 8 Checkliste CHK-01 bis CHK-30 | erfüllt | Datensätze mit Status, Zuständigkeit, Nachweis, Frist und Sperrwirkung; „nachgewiesen“ nur mit gültigem Nachweis passender Art (T-21, T-36) |
| 8 Statusmodell der Prüfpunkte | erfüllt | alle acht Zustände; „nicht anwendbar“ mit Begründung und zweiter Person |
| 9.1 Rollenmodell | teilweise | Berechtigungen `checklist.edit`, `operation.decide`, `central_register.*`, `export.public`; die Zuordnung zu Personen trifft die Anwendung. |
| 9.2 Getrennte Statusachsen | erfüllt | `StatusAxes`; kein `compliant` |
| 9.3 GATE-01 bis GATE-08 | erfüllt | im Backend; die Betriebsentscheidung prüft alle Sperren, die Verzeichnisfreigabe sperrt bei Lücken; eine Fassung mit offenen Angaben gilt nicht als bestätigt (`test_gate02_…`) |

## Abschnitt 10: Datenmodell und Exporte

| Anforderung | Befund | Umsetzung, Grenze |
|---|---|---|
| 10.1 Kernobjekte | teilweise | vorhanden: Tätigkeit, Verzeichnisfassung, DSFA, Szenario, Schutzmaßnahme, Nachweis, Konsultation, Betriebsentscheidung, Regelprofil, Auditereignis. Nicht eigenständig: `SystemDeployment`, `Review` als allgemeine Stellungnahme anderer Stellen. |
| 10.2 Historie und Nachweise | erfüllt | unveränderliche Fassungen, Revisionen, Profilfingerabdruck; keine Fallakten als Nachweis |
| 10.3 Exportprofile | erfüllt | internes VVT (bestehend), Prüfpaket (`review_package`), Austausch über die zentrale Übernahme, öffentliches Muster ohne Inhalte; Status im Prüfpaket |

## Abschnitt 12: Abnahmetests

| Test | Befund | Nachweis |
|---|---|---|
| T-01 bis T-06 | erfüllt | `test_pruefkatalog_register.py` |
| T-07 bis T-16 | erfüllt | `test_pruefkatalog_dsfa.py` |
| T-17 bis T-30, T-33 bis T-36 | erfüllt | `test_pruefkatalog_ablauf.py`, `test_pruefkatalog_web.py` |
| T-31 | teilweise | Browsertest nur mit Tastatur und axe; ein Test mit Screenreader steht aus. |
| T-32 | teilweise | gescheitertes Speichern: Eingabe bleibt, keine Erfolgsmeldung; den Sitzungsablauf verantwortet die Anwendung. |

## Organisatorisch, nicht durch Software lösbar

Beauftragung, Servernutzung und IT-Inventarisierung; Klärung der KPAnG-Zuständigkeit und der
fachrechtlichen Normenkette; Abgleich der Profile mit amtlichen Fassungen, HBDI-Listen und
Hausvorgaben; Zuweisung von Betrieb, Wartung und Regelpflege; Entscheidung, was öffentlich wird.
Die Bibliothek fragt diese Punkte ab und macht sie sichtbar, beantwortet sie aber nicht.
