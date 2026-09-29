# Frontend und Adminbereich für Konto und Mandant

Stand: 29. September 2026. Zielentwurf, noch keine Implementierung.
Ergänzt den [gemeinsamen Standard](konto-mandant-best-practice.md).
Die Nutzeranforderung umfasst ausdrücklich Vue, React und die Administration
von Mandanten, Nutzern, Passwortzuweisung, Rechten und Rollen.

## 1. Gestalterische Richtung

Eine ruhige, hochwertige Verwaltungsoberfläche: klare Typografie, großzügige
Abstände, wenige Akzentfarben und erkennbare Hierarchie. Der Inhalt trägt die
Seite. Profilfoto beziehungsweise Logo schaffen Wiedererkennung; klare Tabellen
und kurze Formulare machen die Administration schnell bedienbar.

Die [Ansichtsskizze](screenshots/konto-mandant-entwurf.svg) konkretisiert die
Richtung für Desktop mit synthetischen Daten. Sie zeigt zwei Zustände desselben
Systems, keine unterschiedlichen Designvarianten. Ein bedienbarer Prototyp und
eine visuelle Abnahme folgen in der Implementierungsphase.

Die [PDF mit 13 GUI-Ansichten](entwuerfe/konto-mandant-gui.pdf) zeigt außerdem
Bildeditor, Webcam, Anlageformulare, Rollen und Begrüßung sowie Mobil-/Dunkeldarstellung.
Sie ist ein statischer Entwurf; die vorhandenen Buttons sind nicht bedienbar.

| Element | Gemeinsame Vorgabe |
|---|---|
| Typografie | Bestehende `--fa-font-sans`; klarer Seitentitel, zurückhaltende Abschnittstitel, gut lesbare Werte |
| Flächen | Neutraler Hintergrund, ruhige Karten, feine Kontur, sparsame Schatten |
| Akzent | Bestehendes Auditcore-Blau für aktive Navigation, Fokus und primäre Aktion |
| Abstände | Vorhandene `--fa-space-*`; gemeinsame Abstände zwischen Label, Eingabe, Hilfe und Fehler |
| Bild | Personenfoto rund, Logo in einer abgerundeten quadratischen Fläche ohne Beschneidungszwang |
| Formulare | Labels oberhalb, Hinweise darunter, maximal zwei Spalten; lange Namen und E-Mail über volle Breite |
| Aktionen | Pro Abschnitt eine eindeutige Hauptaktion, ergänzende Aktionen sekundär; Risiken nicht nur durch Farbe kennzeichnen |
| Status | Text mit zurückhaltendem Badge: Aktiv, Eingeladen, Gesperrt; bei Bedarf Symbol zusätzlich |
| Tabellen | Gemeinsame Tabellenkomponente; Suche, Filter, Sortierung, Seitenwechsel und klare Leerzustände |
| Dunkelmodus | Dieselben Komponenten und Token; keine zweite Layoutfassung |

Als konkrete Designvorgabe für die Referenz: Profilinhalt maximal 960 CSS-Pixel,
Admininhalt maximal 1280 CSS-Pixel, Seitenabstand über vorhandene Abstandstoken.
Die lokale Navigation nutzt auf breiten Seiten 224 CSS-Pixel. Unter 768 CSS-Pixel
stehen Kontextwahl und Abschnittsnavigation über dem Inhalt, Formulare einspaltig.
Diese Werte sind neue Layoutentscheidungen, keine fachlichen Grenzwerte.

Die Oberfläche muss bei 320 CSS-Pixel Breite und vergrößerter Schrift bedienbar
bleiben. Tabellen dürfen bei Bedarf einen beschrifteten horizontalen Scrollbereich
haben; die Hauptaktionen bleiben erreichbar. Die Aktionsleiste darf keine Felder,
Fehler oder fokussierten Bedienelemente verdecken.

## 2. Gemeinsame Navigation

```text
Mein Konto                         Administration
  Profil                             Mandanten          [Plattformebene]
  Kontakt                            Nutzer             [Plattformebene]
  Zugang und Sicherheit              Mitglieder         [Mandantenebene]
                                     Rollen und Rechte
Mandant                              Änderungsprotokoll
  Profil
  Kontakt
  Mitglieder und Zugriff
  Begrüßung
```

Der aktuelle Bereich steht im Seitentitel. Der Geltungsbereich wird zusätzlich
als „Plattform“ oder „Mandant: …“ oberhalb der Daten angezeigt. Ein Wechsel des
Mandanten übernimmt keine Auswahl, keinen offenen Dialog und keinen ungespeicherten
Entwurf still in den neuen Kontext.

„Nutzer“ bezeichnet ein Konto innerhalb des angebundenen Identitätssystems.
„Mitglieder“ bezeichnet dessen Zuordnung zu einem bestimmten Mandanten.
Eine Mitgliedschaft ist kein zweites Konto. Einladungen bestehender Personen
erzeugen keine doppelten Konten. Die Oberfläche verrät Mandantenadministratoren
keine fremden Mitgliedschaften oder nicht freigegebenen Plattformkonten.

## 3. Adminlisten und Detailansichten

| Ansicht | Listeninhalt | Primäre Aktion |
|---|---|---|
| Mandanten | Logo, Anzeigename, Kennung, Status, Mitgliederzahl | Mandant anlegen |
| Nutzer | Foto/Initialen, Anzeigename, Anmeldekennung, Zugangsart, Kontostatus | Nutzer anlegen |
| Mitglieder | Foto/Initialen, Name, Funktion, Rollen, Mitgliedschaftsstatus | Mitglied hinzufügen |
| Rollen | Name, Geltungsbereich, Kurzbeschreibung, Anzahl Rechte, System-/eigene Rolle | Rolle anlegen |
| Änderungsprotokoll | Zeitpunkt, Akteur, Vorgang, Zielobjekt, Ergebnis | Filter anwenden |

Listen haben eine eigene Suchzeile und gezielte Statusfilter. Details öffnen als
vollständige Seite mit Rückkehr zur erhaltenen Suche und Seitenposition. Ein
Zeilenmenü enthält ergänzende Aktionen. Aktionen mit größerer Wirkung erhalten
ausgeschriebene Bezeichnungen, etwa „Mitgliedschaft sperren“ statt „Sperren“.

Die Nutzerdetailseite verwendet denselben Profilbaustein wie „Mein Konto“.
Sie trägt jedoch eindeutig „Nutzer verwalten“ und den Namen der betroffenen Person.
Administrative Aktionen stehen im Bereich „Zugang und Berechtigungen“ und werden
nicht mit dem persönlichen Speichern vermischt. Kontaktdaten und Mitgliedschaften
werden nur im berechtigten Geltungsbereich gezeigt.

Eine Mandantensperre, globale Kontosperre und Mitgliedschaftssperre sind verschiedene
Vorgänge. Der Dialog nennt vor der Bestätigung deren Wirkung. Eine globale
Kontosperre ist Plattformzuständigkeit; ein Mandantenadministrator kann nur den
Zugang zu seinem Mandanten sperren.

## 4. Mandant anlegen

Ein dreistufiger Ablauf hält das Formular überschaubar:

1. **Organisation:** offizieller Name, Anzeigename, Kennung und optional Logo.
2. **Verantwortung und Kontakt:** Organisationskontakt, vorhandene berechtigte
   Person zuordnen oder ersten Mandantenadministrator einladen.
3. **Prüfen und anlegen:** Stammdaten, Verantwortlichkeit und geplanter Zugangsweg
   in einer verständlichen Zusammenfassung anzeigen.

Rückwärtsnavigation erhält den Entwurf. Die Kennung wird vorläufig vorgeschlagen
und serverseitig auf Eindeutigkeit geprüft. Die technische ID wird serverseitig
vergeben. Der Mandant startet im Status „Einrichtung“, bis ein wirksamer
Administrationszugang oder eine ausdrücklich zuständige Plattformadministration
gesichert ist. Danach kann er aktiviert werden.

Mandant, erste Mitgliedschaft und Einladungsauftrag werden konsistent angelegt.
Ein fehlgeschlagener E-Mail-Versand erzeugt keinen zweiten Mandanten bei Wiederholung.
„Mandant angelegt“ und „Einladung versendet“ werden als getrennte Ergebnisse angezeigt.
Der Versandauftrag wird über eine transaktionale Outbox oder einen gleichwertigen
zuverlässigen Adapter ausgeführt; der Bibliothekskern versendet selbst keine E-Mails.

## 5. Nutzer anlegen und Mitglieder hinzufügen

Das gemeinsame Formular zeigt Name, Anmeldekennung beziehungsweise Login-E-Mail,
Zugangsart und vorgesehene Mitgliedschaft. Optionale Profildetails können später
ergänzt werden. Rollen werden mit Beschreibung angeboten, ohne vorausgewählte
administrative Rechte.

- **Neues lokales Konto:** Plattformberechtigte legen ein Konto an; Aktivierung
  erfolgt durch Einladung oder Startpasswort mit Pflichtwechsel.
- **Vorhandene Person:** Mitgliedschaft hinzufügen oder einladen; vorhandenen Zugang
  unverändert lassen und keine globale Passwortneuvergabe durch Mandantenadministratoren.
- **Externes Konto:** an das konfigurierte Identitätssystem anbinden. Kennungen werden
  durch einen geprüften Verknüpfungsablauf zugeordnet, nicht allein durch gleiche E-Mail.
- **Mandantenadministrator:** Einladung in den eigenen Mandanten ist erlaubt, soweit
  das Recht dazu besteht. Die Suche bleibt auf sichtbar berechtigte Personen begrenzt.

Die Einladung zeigt Zielmandant und Rollen. Sie ist erst wirksam, wenn die
Zielidentität geprüft wurde und der einladende Kontext weiterhin berechtigt ist.
Einladung widerrufen, erneut ausstellen und Mitgliedschaft sperren sind getrennte
Aktionen. Ein neuer Link macht den vorherigen ungültig.

### Begrüßungstext des Mandanten

Unter „Mandant → Begrüßung“ kann die zuständige Administration einen eigenen
Begrüßungstext formulieren. Dafür gibt es das gesonderte Recht `tenant.welcome.update`.
Es gehört im Zielstandard zur Mandantenadministration. Die Änderung gilt nur für
den ausgewählten Mandanten; Plattformadministratoren wählen diesen ausdrücklich aus.

Das Formular enthält Überschrift und Text sowie die Auswahl „In Einladungen anzeigen“
und „Beim ersten Öffnen des Mandanten anzeigen“. Beide Verwendungen sind vorbelegt.
Eine zentrale Standardvorlage ist vorhanden und kann wiederhergestellt werden.
Absätze, Listen und Hervorhebungen sind erlaubt; beliebiger HTML-Code ist ausgeschlossen.

Eine Werkzeugleiste fügt die unterstützten Platzhalter Anzeigename der Person,
Mandantenname und hinterlegter Organisationskontakt ein. Leere optionale Werte
erhalten eine neutrale Ersatzdarstellung. Unbekannte Platzhalter werden als
Formularfehler angezeigt, nicht als ausführbare Vorlage interpretiert.

Die Vorschau zeigt getrennt „Einladung“ und „In der Anwendung“ mit synthetischen
Beispieldaten. Persönliche Anrede und Mandantenname werden automatisch eingesetzt.
Der Einladungslink wird als eigener Systembutton ergänzt; der Admin muss ihn nicht
in den Text schreiben. Zugangsart, Linkgültigkeit und erforderliche nächste Schritte
bleiben in einem festen Systemabschnitt erhalten. Bei Startpasswort oder externem
Zugang wird der passende Hinweis gezeigt; die Begrüßung enthält keine Passwörter.

„Änderungen speichern“ übernimmt den Text für zukünftige Einladungen und künftige
erste Begrüßungen. Speichern verschickt keine Nachricht. Beim einzelnen Einladen
kann die berechtigte Person eine zusätzliche persönliche Nachricht ergänzen, ohne
die Mandantenvorlage zu ändern. Die letzte Vorschau vor dem Versand enthält beide
Texte sowie den Systemabschnitt. Diese Nachricht verändert keine vergebenen Rechte.

Einladungsaufträge binden die verwendete Vorlagenrevision und persönliche Nachricht
beim Erstellen; ein späterer Vorlagenwechsel verändert bereits beauftragte Nachrichten
nicht. Die Willkommensansicht wird beim ersten Öffnen einer aktiven Mitgliedschaft
angeboten. „Los geht’s“ bestätigt sie dauerhaft je Mitgliedschaft. Vorlagenänderungen
setzen diese Bestätigung nicht zurück. Der Text bleibt unter dem Mandantenprofil
erneut lesbar; er ist keine Zustimmung zu Vertrags- oder Datenschutzbedingungen.

Vue und React verwenden denselben Editorvertrag, dieselbe Vorschau und dieselben
Texte. Zu prüfen sind Platzhalter, leere Kontakte, Formatierung, Mandantentrennung,
Vorlagenrevision beim Versand, zusätzliche persönliche Nachricht sowie die nur
einmalige Begrüßung pro Mitgliedschaft. Die Vorschau versendet keine Test-E-Mail.

## 6. Passwortzuweisung und Wiederherstellung

**Standard: Die Person setzt ihr Passwort selbst über einen Einladungslink.**
Der Link ist zeitlich begrenzt und einmal verwendbar. Administratoren sehen
Versand- und Annahmestatus, aber kein Passwort. Der rohe Einladungs- oder Resetwert
wird weder in Anwendungslogs noch als lesbarer Datenbankwert gespeichert.

**Alternative für Umgebungen ohne E-Mail: Startpasswort erzeugen.** Die Plattform
erzeugt ein zufälliges Startpasswort und zeigt es der berechtigten Person einmal
zur sicheren Übergabe an. Es wird nicht als dauerhafte Profilinformation gespeichert.
Es läuft nach der zentral festgelegten Frist ab. Die erste Anmeldung erlaubt nur
den Passwortwechsel; normale Fachzugriffe werden bis dahin serverseitig gesperrt.
Eine erneute Ausstellung ersetzt das bisherige Startpasswort.

Bei einem bestehenden Konto heißt die Aktion „Passwort zurücksetzen“. Standardmäßig
wird ein Resetlink versendet. Die Beantragung ändert das Passwort noch nicht.
Nach erfolgreichem Reset werden lokale Sitzungen widerrufen und eine reguläre
Neuanmeldung verlangt. Für einen ausdrücklich administrativen Offline-Reset gelten
erneuter Identitätsnachweis des Administrators, explizite Bestätigung der sofortigen
Zugangswirkung und Pflichtwechsel. Mandantenrechte allein erlauben diesen globalen
Eingriff in ein mehrfach zugeordnetes Konto nicht.

Bei extern verwalteten Konten erscheint stattdessen „Zugang wird zentral verwaltet“.
Auch Administratoren erhalten keine Anzeige bestehender Passwörter. Laufzeiten,
Versuchslimits und Passwortregeln werden zentral festgelegt und im UI verständlich
angezeigt. MFA wird durch einen Passwortreset nicht still abgeschaltet.
Grundlage: [OWASP Forgot Password](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html).

## 7. Rechte und Rollen

Eine Berechtigung beschreibt eine Handlung. Eine Rolle bündelt Berechtigungen.
Die Zuweisung einer Rolle gilt für die Plattform oder für eine konkrete Mitgliedschaft.
Funktion/Dienststellung bleibt davon unabhängig.

Vorgesehene Grundrollen für die Administration:

| Rolle | Geltungsbereich | Aufgabe |
|---|---|---|
| Plattformadministrator | Plattform | Mandanten und Kontolebenszyklus verwalten; keine stillschweigende Freigabe sämtlicher Fachdaten |
| Mandantenadministrator | Ein Mandant | Organisationsprofil, Mitgliedschaften und delegierbare Mandantenrollen verwalten |
| Mitglied | Ein Mandant | Freigegebene Organisationsdaten lesen und eigene Angaben pflegen; Fachrechte werden separat vergeben |

Fachpakete registrieren ihre konkreten Berechtigungen mit Name, Beschreibung und
Geltungsbereich. Rollen wie „Prüfer“ oder „Freigebender“ werden erst aus diesen
Fähigkeiten definiert. Ein generisches Recht „Bearbeiten“ darf nicht pauschal
alle heutigen und zukünftigen Fachmodule freigeben.

Die Rollenbearbeitung zeigt eine nach Fachbereich gruppierte Rechtematrix mit
verständlich beschrifteten Aktionen. Systemrollen sind geschützt; eigene Rollen
können aus einer Vorlage kopiert werden. Vor dem Speichern zeigt die Oberfläche
hinzugefügte und entfernte Rechte sowie betroffene Mitgliedschaften.

Konkrete technische Rechte wären beispielsweise `tenant.profile.update`,
`membership.invite`, `membership.suspend`, `role.assign` und `account.password.reset`.
Sie sind vorgesehene Vertragsnamen, noch keine vorhandenen Exporte.

Es gelten folgende Regeln:

- Standardmäßig kein Zugriff. Jede Operation prüft Berechtigung und Objektkontext auf dem Server.
- Rollenbesitz und Vergaberecht sind getrennt. Ein Administrator darf nur ausdrücklich
  delegierbare Rollen beziehungsweise Rechte vergeben, auch beim Erstellen neuer Rollen.
- Ein Mandantenadministrator kann keine Plattformrolle und keine Rolle eines fremden Mandanten vergeben.
- Mehrere Rollen vereinigen ihre erlaubten Aktionen innerhalb desselben Geltungsbereichs.
  Kontosperre, Mandantensperre, Mitgliedschaftssperre und Objektgrenzen haben Vorrang.
- Einzelne zusätzliche Nutzerrechte und individuelle Verbote entfallen in der ersten Fassung;
  so bleibt die Herkunft der effektiven Rechte nachvollziehbar.
- Neue Rechte erscheinen nicht automatisch in bestehenden eigenen Rollen.
- Rechteentzug wird spätestens bei der nächsten autorisierten Anfrage wirksam;
  langlebige Token und Berechtigungscaches müssen dafür eine serverseitige Revision beachten.
- Die letzte wirksame Administrationszuständigkeit darf nicht versehentlich entfernt werden.
- Jede Rollenänderung wird mit Geltungsbereich protokolliert.

Die Nutzerdetailseite zeigt „Wirksame Rechte“ einschließlich ihrer Herkunft aus
Rollen. Dieser Nachweis ist lesbar, keine zweite Stelle für direkte Rechtevergabe.
Grundlage: [OWASP Authorization](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html).

## 8. Gleichwertige Vue- und React-Frontends

Gemeinsame Texte, Validierung, Berechtigungsdarstellung, Entwürfe und Zustandswechsel
liegen ausschließlich in `@auditcore/ui-core`. Vue und React rendern denselben
Vertrag mit nativen Komponenten. React benötigt zur Laufzeit kein Vue.

Wiederverwendung vorhandener Basisbausteine: `FaButton`/`Button`,
`FaTextField`/`TextField`, `FaBadge`/`Badge`, `FaDialog`/`Dialog`, Icons und Tabelle.
Neue gemeinsam verwendete Bausteine sind Profilkopf, Abschnittsnavigation,
Bildeditor, Speichermeldung, Rollenwahl und Rechteübersicht. Ganze Seiten sind
fertige Bibliothekskomponenten; Anwendungen sollen keine Layoutkopien benötigen.

Die vorgesehenen Seiten heißen `AccountPage`, `TenantPage`, `TenantAdminPage`,
`UserAdminPage` und `RoleAdminPage`, jeweils gemäß bestehender Exportkonvention.
Anlage- und Einladungsabläufe verwenden dieselben Formularbausteine wie die
Detailseiten. Der Komponenten-Generator und das bestehende Paritätsgate sind
verbindlich; keine handgepflegte zweite React-Geschäftslogik.

Anwendungsspezifische Mandantenbereiche werden als zusätzliche Reiter registriert,
zum Beispiel „Operationelles Programm“ in Rechnungslegung. Sie verwenden dieselbe
Gestaltung und benannte eigene Speicherbereiche. Feldumfang, Rechte, Versionierung
und Datenerhalt regelt der Abschnitt
[Anwendungsspezifische Erweiterungen](konto-mandant-best-practice.md#anwendungsspezifische-erweiterungen).
Die bisherige PDF zeigt die gemeinsamen Ansichten; dieser Fachreiter ist darin
noch nicht dargestellt.

Fokus und Tastatur werden bereits im Entwurf berücksichtigt: sichtbare Labels,
erreichbare Menüs, Fokus auf Fehlerzusammenfassung, Fokusführung im Dialog und
Rückkehr zum auslösenden Element. Escape schließt einen Dialog nur unter Beachtung
ungespeicherter Änderungen. Orientierung bietet das
[W3C-Dialogmuster](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/).

## 9. Umsetzung und überprüfbare Abnahme

1. Gemeinsame Controller, Typen, Texte und Stile; synthetischer Referenzadapter.
2. Konto und Mandant einschließlich Bildeditor in Vue, React und Web Components.
3. Adminlisten, Mandantenanlage, Nutzeranlage, Mitgliedschaften und Zugangszuweisung.
4. Rollenbearbeitung, wirksame Rechte, Sperren und Änderungsprotokoll.
5. Backendverträge und Integrationsadapter mit Transaktionen, Rechteprüfung und Sitzungswiderruf.
6. Paketprüfung und Abnahme der Referenz; danach schrittweise Migration der Anwendungen.

Ein Demo-Adapter kann die Bedienung zeigen, ersetzt aber keine Backendabnahme.
Zur Referenz gehören visuelle Vergleichsansichten für Hell/Dunkel, Desktop/Mobil,
lange Namen, leere Listen, fehlende Rechte, Versandfehler und Speicherkonflikte.
Vue und React müssen dieselben Interaktionsfälle bestehen. Automatisierte
Barrierefreiheitsprüfungen werden durch Tastatur- und Fokusprüfung ergänzt.

Zusätzlich zur Profilabnahme werden folgende Fälle geprüft: wiederholte Anlage
ohne Duplikate, Versandfehler nach erfolgreicher Anlage, abgelaufene und mehrfach
benutzte Einladungen, Pflichtwechsel bei Startpasswort, gesperrte Mitgliedschaft,
globaler gegenüber mandantenbezogenem Reset, letzte Administrationszuständigkeit,
unzulässige Rollendelegation und Rechteentzug bei bereits ausgestellten Token.

Für diese Konzeptdatei wurden keine Implementierungstests ausgeführt. Sie definiert
deren spätere Anforderungen und behauptet keine bereits erreichte Funktionsfähigkeit.
