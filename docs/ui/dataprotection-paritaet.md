# Paritätsinventur VVT und DSFA

Vorbild: `regulierung` (`frontend/src/pages/admin/MandantDsgvoSeite.tsx`,
`MandantDsfaAnsicht.tsx`, Stand `ce76e48`) und die Ansicht des
Verarbeitungsverzeichnisses aus `auditcore_dataprotection` 0.4.0
(`render_register_html`). Neu: `<flowaudit-vvt>`, `<flowaudit-dsfa>`
(`@flowaudit/ui`), REST `auditcore_dataprotection.web` 0.5.0.

Legende: ✅ übernommen · ➕ neu/erweitert · ⚠ bewusst anders · ⏳ nicht übernommen.

## Verzeichnis von Verarbeitungstätigkeiten (Art. 30 DSGVO)

| regulierung | neu | |
|---|---|---|
| Deckblatt: Verantwortlicher, DSB (aus Mandantenstammdaten, nur Anzeige) | Name editierbar im Entwurf, Hinweis der Bibliothek bei fehlender Angabe | ⚠ Stammdatenübernahme ist Sache der Anwendung (Inhalt `deckblatt`) |
| Referate konfigurierbar (Chips, hinzufügen/entfernen) | gleich | ✅ |
| Tätigkeiten je Referat, Formular mit allen Feldern | Liste je Referat mit Suche + Detail; Felder und Rechtsgrundlagen aus dem Profil (`GET /profile`) | ✅ ➕ |
| Pflichtangaben lit. a–g (Zweck, Kategorien Betroffene/Daten, Empfänger, Drittland mit Garantien, Löschfristen, TOM) | gleich; Ja/Nein/nicht angegeben statt Kontrollkästchen | ⚠ „nicht angegeben“ ist kein Nein |
| Keine Vollständigkeitsprüfung in der Oberfläche; Excel-Export | Prüfung der Bibliothek (`check_register`) live beim Tippen, je Tätigkeit (Badge), je Feld (`aria-invalid`) und als Liste | ➕ |
| Entwurf speichern, Freigabe durch andere Person | gleich; Vier-Augen-Hinweis vorab, Server prüft; Freigabe nur vollständig | ✅ ➕ |
| Versionshistorie | gleich, mit Status `abgelöst` | ✅ |
| Vorbelegung als Entwurf anlegen | – | ⏳ Vorbelegung ist anwendungsspezifisch (regulierung-Adapter) |
| Export als Excel (XLSX) | Druckansicht (PDF über Druckdialog), Markdown, CSV mit Formelschutz; XLSX weiter über `auditcore_dataprotection.excel` | ⚠ |

## Datenschutz-Folgenabschätzung (Art. 35 DSGVO)

| regulierung | neu | |
|---|---|---|
| Übersicht der Tätigkeiten mit Stand, Ergebnis, „Überprüfung erforderlich“ | gleich (`GET /assessments`) | ✅ |
| Bereichsfilter | Parameter `department` im Vertrag; kein Bedienelement | ⏳ |
| Schritte 1–3 als Reiter | WAI-ARIA-Tabs mit Pfeiltasten | ✅ ➕ |
| Schwellwertanalyse: Muss-Liste, WP-248-Kriterien, KI | Blöcke und Fragen aus dem Profil, Wirkung als Badge, Ja/Nein/Unbekannt, Begründung, Erläuterung | ✅ |
| Vorschau (`vorschauDsfa`) | `POST /calculate`, Vorschau deutlich markiert | ✅ |
| Risikoszenarien: Schutzziel, Schwere, Wahrscheinlichkeit, Maßnahmen, Restwert mit Begründung | gleich; Ergebnis brutto → netto mit Stufe | ✅ |
| Notwendigkeit/Verhältnismäßigkeit, Angaben zur Abschätzung | gleich (Stammdaten aus Profil Schema 2) | ✅ |
| Umsetzungsstand und Maßnahmenplan | – | ⏳ (Vertrag nimmt `measure_status`, `action_plan` an) |
| Vorschlag, Entscheidung mit Abweichungsbegründung, Auflagen | gleich | ✅ |
| Konsultation der Aufsichtsbehörde erfassen | Hinweis wird angezeigt, Erfassung fehlt | ⏳ |
| DSB: Stellungnahme, Votum, Folgerung, Vorlage an Leitung | Dokumentationsmodus: Einholung dokumentieren | ⚠ Profile 2026.10.3; Stellungnahme selbst ⏳ |
| Freigabe (Vier-Augen), Neubewertung, Fassungen | gleich; offene Punkte werden mit der Freigabe dokumentiert | ✅ |
| Bericht als PDF | Bericht als Druckansicht (HTML der Bibliothek) und Markdown | ⚠ PDF über Druckdialog oder `auditcore_dataprotection.pdf` |

## Querschnitt

Deutsche Texte mit echten Umlauten (Englisch teilweise), Dark Mode über
`--fa-*`-Token, Tastaturbedienung, `aria-live` für Meldungen, Fehlermeldungen
des Servers unverändert (`role="alert"`). Bildschirmfotos:
`docs/ui/screenshots/dataprotection-*.png`.
