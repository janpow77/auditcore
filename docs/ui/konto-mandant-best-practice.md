# Einheitlicher Standard für Mein Konto und Mandant

Stand: 29. September 2026. Status: ausgearbeitete Zielvorlage zur Umsetzung.
Die Paket-, Komponenten- und Vertragsnamen unten sind vorgesehen, noch nicht
implementiert. Es wurden keine Anwendungen umgestellt.

## 1. Auftrag und Entscheidung

auditcore erhält einen gemeinsamen Standard für das persönliche Konto, das
Mandantenprofil und den Adminbereich für Mandanten, Nutzer, Zugänge und Rollen.
Alle verwenden dieselbe Gestaltung, dieselben Bedienregeln und gemeinsame
Bausteine. Alle Anwendungen übernehmen diesen Standard später.

Das ergänzende [Frontend- und Adminkonzept](konto-mandant-admin-design.md)
legt Gestaltung, Verwaltungsabläufe und Rechtevergabe fest. Die
[Ansichtsskizze](screenshots/konto-mandant-entwurf.svg) zeigt Profil- und
Adminansicht mit synthetischen Daten; sie ist kein Screenshot einer fertigen Anwendung.

Die ausführliche [GUI-Vorschau als PDF](entwuerfe/konto-mandant-gui.pdf) enthält
13 Ansichten einschließlich Bild-Upload, Webcam, Administration und Begrüßung.
Die [HTML-Druckvorlage](entwuerfe/konto-mandant-gui.html) ist ebenfalls statisch.

Die bisherigen Anwendungen liefern Vorlagen und Migrationsdaten. Ihre
unterschiedlichen Bedienabläufe werden nicht als dauerhafte Varianten fortgeführt.
Es gibt insbesondere keine Profile „Designer-Ansicht“, „Regulierung-Ansicht“
oder „Rechnungslegung-Ansicht“.

Einheitlichkeit bedeutet:

- Gleiche Informationen heißen überall gleich und stehen an derselben Stelle.
- Vue, React und Web Components verwenden dieselben Texte, Stile und Zustände.
- Konto und Mandant verwenden dieselbe Profilseite, Feldgruppen und Aktionsleiste.
- Berechtigungen und externe Datenquellen ändern die Bearbeitbarkeit, nicht das Layout.
- Anwendungen liefern Daten und Integrationsadapter; sie bauen die Formulare nicht nach.
- Die erste Referenz entsteht in auditcore. Die Migration der Anwendungen folgt danach.

Ein Mandant bezeichnet den abgegrenzten Organisations- und Datenbereich einer
Anwendung. Ein Konto bezeichnet eine Person. Ihre Zuordnung erfolgt über eine
Mitgliedschaft. Eine Person kann mehreren Mandanten angehören.

## 2. Gemeinsames Erscheinungsbild

Die vollständige Verwaltung öffnet sich als eigene Seite. Kleine Folgeschritte
wie der Bildeditor oder die Passwortänderung öffnen einen fokussierten Dialog.
Es gibt keine alternative vollständige Kontoverwaltung als anwendungsspezifisches Modal.

Beide Seiten verwenden die vorhandenen `--fa-*`-Designtoken aus
[`tokens.css`](../../packages-js/ui-core/styles/tokens.css): Typografie, Abstände,
Farben, Rundungen, Fokusmarkierungen und Hell-/Dunkeldarstellung.
Ein neutraler Seitenhintergrund und ruhige weiße beziehungsweise dunkle Karten
bilden den Standard. Keine eigenen Farbverläufe oder Formulardesigns pro Anwendung.

Zum Mandanten gehört ein eigener Bereich „Corporate Design“: Logos für helle und
 dunkle Hintergründe sowie Dokumente, Primär- und Akzentfarbe, dazu eine kontrastgeprüfte
Textfarbe, Überschriften- und Textschrift aus einem freigegebenen Katalog sowie
Dokumentkopf und -fuß. Freie CSS-Eingaben und ungeprüfte Schrift-Uploads sind kein
Bestandteil des Formulars. Die Komponentenstruktur bleibt in allen Anwendungen
einheitlich. Bestehende Vorlagendaten werden bei der späteren Migration erhalten.

Die implementierte Bibliothek und ihre Integrationsgrenzen beschreibt
[`account.md`](account.md). Die folgenden Abschnitte bleiben der fachliche Zielentwurf.

Die Seite besteht aus:

1. Titel „Mein Konto“ oder „Mandant“ und eindeutigem Kontext.
2. Profilkopf mit Bild, Name, Unterzeile und kompakten Statusangaben.
3. Abschnittsnavigation, auf kleinen Bildschirmen oberhalb des Inhalts.
4. Formulargruppen mit maximal zwei Spalten, mobil einer Spalte.
5. Gemeinsamer Aktionsleiste „Änderungen verwerfen“ und „Änderungen speichern“.

### Aufbau der beiden Ansichten

```text
MEIN KONTO                              MANDANT

[Foto]  Dr. Alex Beispiel                [Logo]  Prüfbehörde Beispiel
        Prüfer · Referat A                      PB Beispiel · Aktiv
        Mandant: Prüfbehörde Beispiel            Mandantenkennung: pb-beispiel

Profil                                  Profil
Kontakt                                 Kontakt
Zugang und Sicherheit                   Mitglieder und Zugriff

Persönliche Angaben                     Organisationsangaben
Anrede          Titel                   Offizieller Name
Vorname         Nachname                Kurzname        Anzeigename
Anzeigename                             Organisationseinheit

Funktion im aktiven Mandanten            Sitz und Anschrift
Funktion        Organisationseinheit    Straße          Hausnummer
Bearbeiterkürzel Stellenkürzel           Postleitzahl    Ort
                                        Land            Adresszusatz

[Änderungen verwerfen] [Änderungen speichern]
```

Das Beispiel ist synthetisch. Die Navigation unterscheidet nur die fachlich
unterschiedlichen Abschnitte. Feldabstände, Karten, Hilfetexte, Bildeditor,
Fehlermeldungen und Aktionen bleiben gleich.

## 3. Mein Konto: Daten und Zuständigkeit

| Gruppe | Einheitliche Felder | Bedeutung |
|---|---|---|
| Person | Anrede, Titel, Vorname, Nachname, Anzeigename | Persönliche Identität; keine automatische Zerlegung vorhandener vollständiger Namen |
| Foto | Bildreferenz, Ausschnitt, Bildversion | Persönliches Profilfoto; Initialen als Ersatz |
| Funktion im aktiven Mandanten | Funktion/Dienststellung, Organisationseinheit, Bearbeiterkürzel, Stellenkürzel | Angaben der Mitgliedschaft; können zwischen Mandanten verschieden sein |
| Kontakt im aktiven Mandanten | Dienstliche E-Mail, Telefon, Mobiltelefon | Berufliche Erreichbarkeit für diese Mitgliedschaft |
| Zugang | Anmeldekennung, Anmeldeverfahren, verifizierte Login-E-Mail, soweit verwendet | Getrennt von Kontakt-E-Mail; Passwort niemals Bestandteil des Profilmodells |
| Berechtigungen | Zugeordnete Rollen | Nur lesbar auf der eigenen Kontoseite; Änderung über Mitgliederverwaltung |

Der Anzeigename ist erforderlich. Getrennte Vor- und Nachnamen bleiben optional,
damit auch bestehende und internationale Namen unverändert darstellbar sind.
Anrede und Titel sind freiwillig. Fehlende Werte werden als „Nicht angegeben“
angezeigt und im Bearbeitungsformular leer dargestellt.

Die Person pflegt ihre persönlichen Angaben und beruflichen Kontaktdaten selbst.
Organisationszuordnung, Funktion, Kürzel und Rollen werden durch die zuständige
Mitgliederverwaltung gepflegt. Diese Trennung ist der vorgeschlagene gemeinsame
Zielstandard, keine Behauptung über die heutigen Berechtigungen.

Extern verwaltete Angaben erscheinen mit „Wird zentral verwaltet“ und bleiben
lesbar. Der Server benennt die zuständige Quelle; die Oberfläche erfindet keine
Bearbeitungsmöglichkeit. Eine Funktion wie „Prüfer“ verleiht keine technische Rolle.

Bei mehreren Mitgliedschaften zeigt die Seite ausdrücklich den aktiven Mandanten.
Persönliche Änderungen gelten innerhalb des angebundenen Kontos; Änderungen an
dienstlichen Kontakten gelten für die ausgewählte Mitgliedschaft. Daraus folgt
keine automatische Synchronisation zwischen den Repositories oder Anmeldesystemen.

## 4. Mandant: Daten und Zuständigkeit

| Gruppe | Einheitliche Felder | Bedeutung |
|---|---|---|
| Identität | Offizieller Name, Kurzname, Anzeigename | Offizieller Name und Anzeigename erforderlich; Anzeigename beim Anlegen mit offiziellem Namen vorbelegt |
| Kennung | Unveränderliche technische ID, Mandantenkennung | Die ID bestimmt die Zuordnung; Namen dienen nie als Zugriffsschlüssel |
| Organisation | Organisationseinheit | Bezeichnung des organisatorischen Bereichs |
| Bild | Logo oder Wappen, Bildreferenz, Bildversion | Organisationszeichen; Ersatzdarstellung mit Initialen |
| Anschrift | Straße, Hausnummer, Adresszusatz, Postleitzahl, Ort, Land | Zusammengehörige optionale Anschrift; ländergerechte Eingaben |
| Kontakt | Allgemeine E-Mail, Telefon, Website, Ansprechperson und deren Funktion | Funktionskontakt getrennt von persönlichen Mitgliedskontakten |
| Status | Einrichtung, aktiv, inaktiv | Sichtbar; Änderung nur mit gesondertem Recht; Einrichtung vor gesicherter Administrationszuständigkeit |
| Zugriff | Mitglieder, zugeordnete Rollen | Aus demselben Mandantenkontext; keine eigenen Mandantenpasswörter |
| Begrüßung | Überschrift, formatierter Text, Verwendung in Einladung und Anwendung | Vom berechtigten Admin je Mandant pflegbar, mit Vorschau und Standardvorlage |

Mitglieder lesen die für sie freigegebenen Organisationsstammdaten. Berechtigte
Mandantenverantwortliche bearbeiten Stammdaten und Logo. Die Mitgliederliste und
Rollenvergabe benötigen eigene Rechte; das Lesen des Mandantenprofils gewährt sie
nicht automatisch. Die Plattformverwaltung legt Mandanten an und verwaltet ihren Status.

Die Rollenbezeichnungen aus bestehenden Anwendungen werden bei der Migration auf
konkrete Fähigkeiten abgebildet, nicht durch einen Vergleich mit dem Text „Admin“.
Ein Nutzer darf sich über die eigene Kontoseite weder weitere Mandanten noch
zusätzliche Rechte zuordnen. Es muss mindestens eine wirksame Zuständigkeit für
die Mandantenadministration erhalten bleiben, einschließlich einer ausdrücklich
konfigurierten Plattformadministration als möglicher Rückfallebene.

Bankverbindung, Förderprogramme, Sektoren, Aktenzeichenmuster, Datenschutzverfahren
und Dokumentgestaltung gehören in benannte Facherweiterungen. Sie erscheinen nach
den gemeinsamen Abschnitten und verändern deren Felder und Bedienung nicht.
Mandanten- und Nutzeranlage, Einladungen, Passwortzuweisung sowie Rechte und Rollen
sind Bestandteil der gemeinsamen Referenz; Einzelheiten stehen im
[Adminkonzept](konto-mandant-admin-design.md). Endgültige Löschverfahren bleiben
wegen ihrer Abhängigkeit von Fachdaten und Aufbewahrung außerhalb der ersten Fassung.

### Anwendungsspezifische Erweiterungen

Anwendungen können zusätzliche Fachbereiche am Mandanten registrieren. Diese
erscheinen als weitere Reiter nach den gemeinsamen Bereichen und verwenden
dieselben Feld-, Tabellen-, Fehler- und Aktionsbausteine. Kernfelder werden
dadurch weder umbenannt noch doppelt angelegt. Die Registrierung erfolgt durch
die Anwendung beziehungsweise ein Fachpaket; sie ist kein frei programmierbarer
Formularbaukasten für Administratoren.

Beispiel Rechnungslegung: Der zusätzliche Reiter heißt „Operationelles Programm“.
Grundlage sind die vorhandenen `MandantProgrammdaten` in
`app/frontend/src/api/mandanten.ts` der Anwendung, insbesondere:

| Gruppe | Vorhandene Angaben |
|---|---|
| Programm | CCI-Nummer, Bezeichnung, Fonds, Mitgliedstaat, Regionskategorie |
| Zeitraum | Erstes und letztes Jahr, Förderfähigkeit von/bis, Geschäftsjahre von/bis |
| Genehmigung | Nummer und Datum des Kommissionsbeschlusses |
| Prioritäten | Wiederholbare Liste mit Nummer und Name |

Diese Felder werden aus dem bestehenden Fachmodell übernommen. Fachliche
Pflichtfelder, Auswahlwerte und Prüfregeln kommen aus Rechnungslegung beziehungsweise
dem zuständigen Fachpaket; die Kontobibliothek erfindet keine Förderregeln.
Der heutige Vertrag enthält einen Programmdatensatz je Mandant. Eine spätere
Mehrprogrammverwaltung braucht eine ausdrückliche Erweiterung des Datenmodells.

Jede Erweiterung registriert eine stabile Kennung, etwa
`rechnungslegung.operational_program`, eine Schemaversion, Titel, Reihenfolge,
typisierte Daten, Validierung, Lese-/Schreibrechte und einen Lade-/Speicheradapter.
Rechte werden auch serverseitig je Mandant geprüft. Ein Mandantenadministrator
erhält neue Fachrechte nicht automatisch allein durch Installation einer Erweiterung.

Die Oberfläche benutzt den gemeinsamen Entwurfs- und Speichercontroller. Ein
zusätzlicher Fachreiter bildet einen ausdrücklich benannten eigenen Speicherbereich,
beispielsweise „Operationelles Programm speichern“. Beim Wechsel in einen anderen
Speicherbereich greift die gemeinsame Behandlung ungespeicherter Änderungen.
Die Oberfläche behauptet keine atomare Speicherung von Stammdaten und Fachdaten,
wenn deren Adapter unterschiedliche Transaktionen verwenden.

Erweiterungsdaten dürfen in bestehenden Fachtabellen verbleiben. Änderungen an
Kernfeldern oder anderen Erweiterungen überschreiben sie nicht. Ist eine Erweiterung
nicht installiert, bleiben ihre Daten erhalten; unbekannte Versionen werden nicht
still neu interpretiert. Migrationen sind explizit und versioniert.

Gemeinsame Felddefinitionen und Fachlogik liegen im zuständigen UI-Kern/Fachpaket.
Vue und React stellen denselben zusätzlichen Reiter mit derselben Funktionalität
dar. Komplexe Bereiche wie Prioritätenlisten können eigene Fachkomponenten nutzen,
die weiterhin dem gemeinsamen Design und Paritätsverfahren folgen.

## 5. Einheitliche Bedienregeln

- Profil und Kontakt bilden einen gemeinsamen Entwurf. Abschnittswechsel erhält ihn.
- Änderungen werden erst mit „Änderungen speichern“ wirksam. Kein verstecktes Autosave.
- „Änderungen verwerfen“ setzt Formular und Bild auf den zuletzt gespeicherten Stand zurück.
- Beim Verlassen mit Änderungen stehen „Weiter bearbeiten“ und „Änderungen verwerfen“ zur Wahl.
- Ohne Änderungen ist Speichern deaktiviert. Während einer Anfrage werden doppelte Aufträge verhindert.
- Ladefehler, leere Werte, fehlende Rechte, Speichervorgang, Erfolg und Konflikt sind eigene Zustände.
- Fehler stehen direkt am Feld; eine Zusammenfassung führt nach dem Speicherversuch zum ersten Fehler.
- „Änderungen gespeichert“ erscheint erst nach bestätigter Speicherung aller Bestandteile.
- Bei Verbindungsfehlern bleibt der Entwurf erhalten. Wiederholung erzeugt keine doppelten Bildzuordnungen.
- Bei zwischenzeitlichen Änderungen durch andere Personen wird nichts still überschrieben:
  „Die Daten wurden inzwischen geändert. Bitte laden Sie den aktuellen Stand.“
  Der eigene Entwurf bleibt zum Vergleichen verfügbar.
- Passwort, Login-E-Mail, Rollen und Status sind gesonderte Vorgänge mit eigenen Ergebnissen.

Die Formulare verwenden sichtbare Beschriftungen, semantische Gruppen, verständliche
Hinweise und programmatisch zugeordnete Fehler. Erfolg und Ladezustände werden auch
assistiven Technologien mitgeteilt. Grundlage sind die
[W3C-Formularhinweise](https://www.w3.org/WAI/tutorials/forms/) und
[W3C-Hinweise zu Rückmeldungen](https://www.w3.org/WAI/tutorials/forms/notifications/).

## 6. Ein Bildeditor für Foto und Logo

Beide Bildtypen verwenden dieselbe Implementierung und dieselben Aktionen:
Datei wählen, Vorschau, Zoom, Position, Drehen, Zurücksetzen, Übernehmen, Entfernen.
Beim Personenfoto kommt „Foto aufnehmen“ hinzu. Die Kamera startet nur nach
bewusster Betätigung und wird beim Schließen oder Wechseln zuverlässig gestoppt.
Bei fehlender Kamera oder abgelehnter Berechtigung bleibt der Datei-Upload verfügbar.
Es wird ausschließlich Video für die lokale Vorschau angefragt, kein Mikrofon.
Erst die bewusst ausgelöste Fotoaufnahme wird als Bildentwurf weiterverarbeitet;
ein laufender Kamerastream wird nicht hochgeladen. Die spätere Webanwendung
benötigt einen sicheren Browserkontext, im Betrieb üblicherweise HTTPS, und
die Kamerafreigabe des Nutzers; siehe
[MDN getUserMedia](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia).

Das Personenfoto wird quadratisch zugeschnitten und im Profilkopf rund dargestellt.
Beim Logo gilt standardmäßig „Vollständig einpassen“ mit erhaltenem Seitenverhältnis
und Transparenz. Wappen werden nicht automatisch rund beschnitten. Ein freiwilliger
Zuschnitt ist möglich. Der Editor zeigt jeweils die spätere Darstellung an.

Verschieben und Zoom sind neben Zeigerbedienung auch über beschriftete
Tastaturbedienelemente erreichbar. Ein optionales Raster wird nur als Bearbeitungshilfe
angezeigt. Der Bildeditor verändert zunächst den Entwurf; „Übernehmen“ speichert
noch nicht das gesamte Profil.

Die Bildverarbeitung korrigiert die Orientierung, prüft tatsächlichen Bildinhalt,
Dateigröße und Pixelzahl, entfernt Metadaten und erzeugt neue Rasterdateien.
Die erste Fassung unterstützt JPEG, PNG und WebP. Grenzwerte werden zentral im
Bibliotheksvertrag festgelegt und identisch im Client angezeigt sowie serverseitig
erzwungen; alte unterschiedliche App-Limits sind kein Zielstandard.
Grundlage: [OWASP File Upload](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html).

Gespeichert werden ein bereinigtes Ausgangsbild sowie normalisierte Ausschnittdaten
und eine daraus erzeugte Darstellung. Rohdateien einschließlich EXIF werden nicht
dauerhaft aufbewahrt. Späteres Nachjustieren nutzt das bereinigte Ausgangsbild.
Der Ausschnitt bezieht sich auf dessen orientierte Bildkoordinaten, nicht auf CSS-Prozentwerte.

Ein Upload wird zuerst als befristeter Entwurf gespeichert. Erst der erfolgreiche
Profil-Commit verknüpft Bild und Daten gemeinsam. Das alte Bild bleibt bis dahin
gültig; abgebrochene Uploads werden bereinigt. Nach Entfernen erscheint die
Ersatzdarstellung. Interne Dateipfade werden nicht an den Client ausgegeben.

## 7. Zugang und Mandantengrenzen

Bei lokalem Passwort zeigt der Dialog aktuelles Passwort, neues Passwort und
Wiederholung. Passwortmanager und Einfügen bleiben erlaubt. Die Prüfung und
Hashbildung verwenden `auditcore_auth`; die zentrale Passwortregel wird vom
Backend geliefert und dort erzwungen. Es wird keine zweite Kryptografie eingeführt.

Der Zielablauf verlangt erneuten Identitätsnachweis, widerruft nach erfolgreicher
Änderung andere lokale Sitzungen einschließlich erneuerbarer Zugänge und erneuert
die aktuelle Sitzung. Ein Adapter muss den Widerruf tatsächlich durchsetzen können;
eine bloße Erfolgsmeldung vor weiter gültigen Sitzungen erfüllt den Zielvertrag nicht.
Bei extern verwaltetem Zugang führt dieselbe Stelle zur externen Kontoverwaltung.
Die Login-E-Mail wird über einen separaten Verifikationsablauf geändert; eine Änderung
der Kontakt-E-Mail ändert nie still die Anmeldung.
Grundlage: [OWASP Authentication](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html).

Jeder Lese- und Schreibzugriff prüft serverseitig Identität, Mandantenzugehörigkeit
und konkrete Berechtigung. Der ausgewählte Mandant im Browser allein autorisiert
keinen Zugriff. Bilder, temporäre Uploads, Caches und Hintergrundaufträge erhalten
denselben Mandantenbezug. Beim Mandantenwechsel werden alte Entwürfe bewusst
abgeschlossen oder verworfen und verspätete Antworten dem alten Kontext zugeordnet.
Grundlage: [OWASP Multi Tenant Security](https://cheatsheetseries.owasp.org/cheatsheets/Multi_Tenant_Security_Cheat_Sheet.html).

Änderungsereignisse enthalten Akteur, Zielobjekt, Mandantenkontext, Zeitpunkt und
geänderte Feldnamen. Passwörter, Token, Bildbytes und vollständige Kontaktwerte
werden nicht in allgemeinen Anwendungslogs abgelegt.

## 8. Technischer Zielvertrag

Die neue Python-Distribution heißt vorgeschlagen `auditcore_account`. Sie umfasst
Personenprofil, Mandantenprofil, Mitgliedschaft, Rollen und administrative Abläufe
als getrennte Modelle innerhalb einer Bibliothek. `auditcore_auth` bleibt für
Authentifizierungsprimitive zuständig. Der zusätzliche Umfang ändert nicht die
Trennung von fachlichen Verträgen und anwendungsspezifischer Persistenz.

| Schicht | Vorgesehene Verantwortung |
|---|---|
| `auditcore_account` | `PersonProfile`, `TenantProfile`, `MembershipProfile`, Änderungsverträge und Validierung; frameworkfreier Kern |
| Optionaler Bildadapter | Bildverarbeitung mit Pillow; explizite Ein-/Ausgaben, keine fest eingebauten App-Verzeichnisse |
| App-Adapter | Persistenz, Transaktionen, Berechtigungsprüfung, Sitzungswiderruf, externes Identitätssystem und Bildspeicher |
| `@auditcore/ui-core`, Gruppe `account` | Gemeinsame Typen, Texte, Controller, Entwurfszustand, Bildgeometrie und Stile |
| `@auditcore/ui` und `@auditcore/ui-react` | `AccountPage`, `TenantPage`, gemeinsame Profil- und Bildbausteine nach bestehender Namenskonvention |
| Web Components | Dieselben Fähigkeiten über das vorhandene Registrierungsverfahren |

Benötigte Operationen: eigenes Profil laden/ändern, Mandantenprofil laden/ändern,
Bild vorbereiten, Passwort ändern und Login-E-Mail-Änderung anstoßen sowie die
Anlage-, Einladungs-, Sperr- und Rollenoperationen des Adminkonzepts. Gemeinsame
Semantik ist verbindlich; bestehende HTTP-Pfade können zunächst Adapter abbilden.

Jede Profilantwort enthält Objektkennung, Revision, Daten, Bearbeitungsrechte und
Herkunft extern verwalteter Felder. Änderungen enthalten die Ausgangsrevision
und nur geänderte Felder: nicht vorhanden bedeutet unverändert, `null` bedeutet
ausdrücklich löschen. Leerzeichenbereinigung ersetzt diese Unterscheidung nicht.
Unbekannte oder nicht erlaubte Felder werden zurückgewiesen.

Die bereinigte Bildreferenz wird mit derselben Profilrevision verknüpft. Fehler
haben stabile Codes und Feldbezüge, unter anderem Validierung, Konflikt, fehlendes
Recht, externer Zugang und ungültiges Bild. Übersetzungen stehen zentral im UI-Kern.

Die Anwendung darf keine eigenen Kernfelder, Bezeichnungen, CSS-Kopien oder
Speicherabläufe einführen. Fachliche Erweiterungen benutzen einen benannten
Erweiterungspunkt. Änderungen am gemeinsamen Standard erfolgen in auditcore.
Das entspricht dem vorhandenen
[UI-Beitragsverfahren](beitragen.md) und der
[Paketarchitektur](../architecture/ADR-001-multi-package-monorepo.md).

## 9. Referenz und Abnahme vor der Migration

Die Referenz wird zuerst ausschließlich in auditcore gebaut. Sie enthält dieselben
synthetischen Daten in Vue, React und Web Components: ein vollständiges und ein
unvollständiges Konto, zwei Mandanten, mehrere Mitgliedschaften sowie bearbeitbare
und extern verwaltete Angaben. Hinzu kommen Adminlisten, Anlageformulare,
Einladungszustände, Begrüßungseditor mit Vorschau und Rollenbearbeitung. Konto, Mandant und Adminbereich werden
in Hell/Dunkel und schmaler/breiter Darstellung gezeigt. Der Demo-Adapter darf keine
echten Nutzerdaten verwenden.

| Abnahmefall | Erwartung |
|---|---|
| Framework-Parität | Gleiche Texte, Reihenfolge, Zustände und sichtbare Ergebnisse in Vue und React; Web-Component-Einbindung geprüft |
| Formular | Speichern, Verwerfen, Fehler und Navigation erhalten beziehungsweise verwerfen genau den angezeigten Entwurf |
| Foto und Logo | Derselbe Editor; Vorschau entspricht gespeichertem Ergebnis; Logo bleibt vollständig darstellbar |
| Abbruch und Wiederholung | Keine unbeabsichtigte Bildänderung, keine verwaisten dauerhaften Uploads und kein falscher Erfolg |
| Parallelbearbeitung | Veraltete Revision wird erkannt; kein verlorenes Update |
| Kontozugang | Falsches aktuelles Passwort bleibt wirkungslos; Sitzungswiderruf und externer Zugang verhalten sich wie ausgewiesen |
| Rechte und Mandantentrennung | Manipulierte Objekt-/Mandantenkennungen und Uploadreferenzen gewähren keinen Fremdzugriff |
| Bedienbarkeit | Tastatur, Fokusführung, verständliche Feldfehler und Kamera-Abbruch funktionieren |
| Migrationserhalt | Bestehende Namen, Bilder, Rollen, Kontakte und fachliche Erweiterungen gehen nicht verloren |

Vor Implementierungsabschluss: vorhandenes `auditcore-runner`-Profil ausführen,
Maschinenbericht zuerst auswerten und zusätzliche paketbezogene Prüfungen sowie
UI-Paritätsgate gemäß Repositoryregeln durchführen. Ein benötigtes neues Paketprofil
wird bei der Implementierung ergänzt. Screenshots und Testergebnisse werden erst
nach tatsächlicher Ausführung als Nachweise abgelegt.

Danach werden Rechnungslegung, Regulierung und audit_designer auf die Referenz
umgestellt. Unterschiede in Daten und Rechten werden über dokumentierte Migrationen
aufgelöst. Verhaltensänderungen wie Sitzungswiderruf oder neue Feldzuständigkeiten
werden ausdrücklich geprüft; sie dürfen nicht als bloßer Austausch der Oberfläche gelten.

## 10. Vorhandene Grundlagen und Prüfstand

- audit_designer: Namensdetails und getrennte Einstellungen, insbesondere
  [BenutzerEinstellungenView](https://github.com/janpow77/audit_designer/blob/aa71ce1b296564fd386605b4d96f80f6cd7a61e8/frontend/src/views/BenutzerEinstellungenView.vue),
  [Profiltypen](https://github.com/janpow77/audit_designer/blob/aa71ce1b296564fd386605b4d96f80f6cd7a61e8/frontend/src/types/auth.ts) und
  [PasswortPanel](https://github.com/janpow77/audit_designer/blob/aa71ce1b296564fd386605b4d96f80f6cd7a61e8/frontend/src/components/einstellungen/PasswortPanel.vue).
- Regulierung: lokaler Stand von `frontend/src/pages/MeinProfil.tsx`,
  `frontend/src/pages/admin/MandantenTab.tsx`, `backend/app/schemas/user_profil.py`
  und `backend/app/services/profilbild.py`.
- Rechnungslegung: lokaler Stand von `app/frontend/src/components/MeinProfilDialog.vue`,
  `app/frontend/src/api/mandanten.ts` und `app/backend/app/services/profilbild.py`.
- auditcore: bestehende UI-Pakete, Designtoken, `auditcore_auth`, Architekturregel
  und Inventurbericht `docs/reports/inventory-summary.json`. Dessen globale Inventur
  vom 22. September ist als teilweise abgeschlossen gekennzeichnet; sie ersetzt
  keine aktuelle vollständige Prüfung aller Repositories.

Diese Änderung enthält die Zielvorlage, das ergänzende Adminkonzept und eine statische
Ansichtsskizze. Lokale Dokumentlinks und SVG-XML wurden geprüft; die Skizze wurde
im Browser gerendert und visuell kontrolliert. Quellen und vorhandene
Strukturen wurden gelesen; eine laufende Referenzoberfläche, Sicherheitsabnahme
oder bestandene Implementierungstests werden damit nicht behauptet. Das vorhandene
Runner-Profil wurde in der Voruntersuchung gelesen; für diese Dokumentationsänderung
wurde kein Runner-Lauf durchgeführt.
