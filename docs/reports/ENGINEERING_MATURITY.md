# Softwaretechnische Reifegradbewertung

Stand: 22. September 2026. Qualitative Engineering-Bewertung, keine Zertifizierung.
Bezug: veröffentlichte Preview 0.1.0 und lokal geprüfte PDF-/Excel-Erweiterungen
für Invoice/Reporting 0.2.0. Ein Commit oder Merge ist keine Veröffentlichung
dieser neuen Artefakte. CI-/Merge-Nachweise werden im zugehörigen PR festgehalten.

## Urteil

**Das Vorgehen besitzt eine belastbare technische Grundlage. Die Bibliotheken
haben den Stand einer technisch geprüften Preview. Eine vollständige praktische
Bewährung in migrierten Fachanwendungen ist noch nicht belegt.**

Architektur, nachvollziehbare Extraktion, differenzierte Policyprüfung und reale
Paketinstallation sind bereits gut entwickelt. Die größte offene Strecke liegt
zwischen installierbarer Bibliothek und kontrolliert umgestellter Anwendung.
Die Anzahl der Tests oder Paketnamen ersetzt diesen Nachweis nicht.

## Einzelbewertung

| Bereich | Aktueller Reifegrad | Belege und praktische Grenze |
|---|---|---|
| Architektur/Vorgehen | Gut strukturiert, nachträglich präzisiert | Mehrpaket-Monorepo, klar getrennte Anwendungen, selektive Abhängigkeiten und vier Plattformwerkzeuge. Der anfängliche Ein-Projekt-Ansatz und eine zu schmale Kandidatenliste mussten korrigiert werden. |
| Plattform `auditcore` | Technisch geprüfte Plattform-Preview | Installierbar, typgeprüft, CI, FrameworkPolicyProvider, Inventar, Migration/Rollback und reale pip-/APT-Prüfungen. Nicht jede externe Integration oder echte Anwendungsmigration ist abgeschlossen. |
| `auditcore_dummygenerator` 0.1.0 | Technisch geprüfte Fachbibliothek | 79 lokale Tests, 58 Originalfälle, eigene Distribution, bestätigte öffentliche Installation. Zwei dokumentierte Komplexitätswarnungen; synthetische Werte sind nicht automatisch fachlich gültige Realweltkennungen. |
| `auditcore_invoicegenerator` | 0.1.0 veröffentlichte Preview; 0.2.0 geprüfter Ausbau | 265 Tests für den Ausbau, tatsächlich gelesene/gerenderte PDFs, vollständige Quality-Gates PASS. Zweck sind synthetische Testrechnungen. PDF nutzt begrenzten Windows-1252-Zeichensatz und definierte Ressourcenlimits; keine Zusage eines allgemeinen Rechnungslegungssystems. |
| `auditcore_reporting` | 0.1.0 kleiner veröffentlichter Kern; 0.2.0 geprüfter Ausbau | 88 Tests, echte XLSX-Ausgabe, Formelschutz, Limits, kompatible API und vollständige Quality-Gates PASS. ZIP/XML-/Microsoft-SDK-Schemaprüfung bestanden; nativer Excel-Öffnungs-/Ausführungstest NOT_EXECUTED. |
| VVT-/DSFA-Bibliothek | Konkret belegter Entwurf | Erstellung, Bearbeitung, Berechnung, Versionierung und Export sind im Auftrag. Der vorhandene reine Berechnungskern aus regulierung wurde mit 19 Originaltests und 129 zusätzlichen Fällen charakterisiert. Ein vollständiges installiertes `auditcore_dataprotection` existiert noch nicht. |
| Harvester-/weitere Analysepakete | Inventarisierte Kandidaten | Alle 71 eigenen GitHub-Repositories eingeordnet, konkrete Quellen/Consumer benannt. Das ist keine vollständige semantische Analyse aller Sprachen und kein Beleg bereits implementierter neuer Adapterbibliotheken. |
| Anwendungsintegration/Betrieb | Noch nicht vollständig nachgewiesen | Vollständig migrierte reale Anwendungen: 0. Isolierte Consumerprüfungen, Pakettests und eine systemd-Testanwendung sind enger begrenzte Nachweise. |

## Was am Vorgehen stark ist

- Bestehende Implementierungen und Originalausgaben werden vor Änderungen
  untersucht. Exakte Characterization zeigte etwa die Python-3.11-/3.12-
  Fließkommaabweichung, ohne anschließend die Rechnungslogik still zu ändern.
- Fachliche Grenzen steuern Paketgrenzen. Renderer sind Extras; Invoice zieht
  gezielt Dummy nach, Reporting und die Plattform werden nicht mitinstalliert.
- Installation ist ausgeführt: öffentliche 0.1.0-Wheels und signierte APT-Pakete,
  für den 0.2.0-Ausbau lokale gemischte Paketversionen sowie optionale Renderer.
  Der Zielserver benötigt dafür keine Python-/Node-Buildumgebung.
- Policy-Nachweise sind an Quelle, Kontext und Frameworkrevision gebunden.
  UNKNOWN, nicht anwendbar, Review und bestandene technische Prüfung bleiben
  unterscheidbar. Ein Library-PASS wird nicht auf die Anwendung übertragen.
- Negativprüfungen finden konkrete Fehler. Die XLSX-Schemaprüfung entdeckte
  eine Font-Elementreihenfolge, die korrigiert und erneut geprüft wurde.
  Das Review der Releasevorbereitung fand eine unvollständige Bindung optionaler
  Nachweise an Wheel/Version; exakte Closure-/URL-/Hashprüfung und Negativtests
  sichern jetzt diesen Fall.
- Provenienz und Rechte werden quellspezifisch geführt. Die MIT-Freigabe zweier
  Kerne wird nicht automatisch auf weitere private Quellen übertragen.

## Wesentliche verbleibende Risiken

1. **Reale Integration:** Noch fehlt ein abgeschlossener Durchlauf mit einer
   tatsächlich umgestellten Fachanwendung, ihren Berechtigungen, Konfigurationen,
   Regressionen und Rückkehr zum vorherigen Stand. Bis dahin ist die praktische
   Wiederverwendbarkeit nur teilweise bewiesen.
2. **Fachliche Richtigkeit:** Characterization beweist Verhaltensgleichheit.
   Eine geerbte DSFA-Schwelle, Maßnahmenwirkung oder MUS-Formel wird dadurch
   nicht fachlich bestätigt. Der DSFA-Kern zeigt außerdem Vertragsprobleme bei
   direkten Aufrufen mit unvollständigen/doppelten Antworten oder Netto-Nullwerten.
   Validierungen des bestehenden Verwaltungsadapters dürfen bei der Extraktion
   nicht verloren gehen. Das ist keine pauschale Aussage über dessen produktive UI.
3. **Releasepflege:** Langfristige Unterstützung, Abkündigungen, Sicherheitsupdates,
   getestete Consumer-Versionen und Verantwortlichkeiten benötigen einen festen
   Betriebsvertrag. GitHub statt PyPI ist dabei kein grundsätzlicher Reifemangel.
   Die vorhandenen Releases und APT-Signaturen ersetzen diese Pflege nicht.
4. **Nachweispflege:** Umfangreiche historische Dokumente können aktuellen Aussagen
   widersprechen. Zwei solche Stellen wurden jetzt in CONTRIBUTING und der
   Invoice-Profilversionierung korrigiert. Paketstand, Profilstand, CI und
   veröffentlichter Artefaktstand müssen weiterhin klar getrennt geführt werden.
5. **Breite vor Tiefe:** Zu viele gleichzeitige neue Pakete würden API-, Test- und
   Wartungsaufwand erhöhen. Ein konkreter erster Consumer ist wichtiger als eine
   möglichst vollständige Namensliste. Gemeinsam abstammende Kopien sind noch
   keine unabhängig bestätigten Consumerverträge.

## Empfohlene nächste Arbeit

1. Einen überschaubaren echten Consumer vollständig umstellen und dessen
   tatsächliche Funktionspfade, Rechte, Regression und Rollback nachweisen.
2. `auditcore_dataprotection` als zusammenhängende Funktion umsetzen: eigenes
   Register und eigene DSFA erstellen **und berechnen**, sichere Versions- und
   Freigaberegeln, unbekannte Angaben sichtbar halten, ein realer Consumer.
3. Danach eine begrenzte Harvesterfamilie mit einem konkreten Quelladapter
   implementieren und integrieren. Originalantworten, Pagination, Teilfehler,
   Aktualität und Quellenrechte explizit testen.
4. Vor einer stabilen 1.0-Zusage API-/Versionspolitik, Sicherheitsupdates,
   Verantwortlichkeiten und unterstützte Consumerstände festlegen. Die Freigabe
   folgt belegtem Funktionsumfang und Nutzungserfahrung, nicht der Versionsnummer.

## Nachweise

- [Veröffentlichte Pakete und tatsächliche Grenzen](DOMAIN_PACKAGES_REPORT.md)
- [Öffentliche Installation 0.1.0](domain-public-installation.json)
- [Vollständige Repository-Abdeckung](../architecture/REPOSITORY_PACKAGE_COVERAGE.md)
- [Paketplan mit DSFA-Berechnung](../architecture/DOMAIN_PACKAGE_PLAN.md)
- Lokal: `.auditcore/domain-packages-v02/result.json`,
  `.auditcore/optional-renderers-v02/result.json`,
  `.auditcore/invoice-evidence/pdf-result.json`,
  `.auditcore/reporting-v02/quality-root-final.json`,
  `.auditcore/reporting-v02/office-validation-final.log`,
  `.auditcore/dataprotection-characterization/result.json`.

Die lokalen Nachweise sind keine öffentlichen Downloadadressen. Nicht ausgeführte
Native-Office-, Produktions- und Vollmigrationsprüfungen werden nicht als PASS geführt.
