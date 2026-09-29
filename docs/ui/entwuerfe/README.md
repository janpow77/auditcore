# GUI-Ansichten: Konto, Mandant und Administration

## Implementierte Bibliothek

[PDF mit 12 implementierten Ansichten](konto-bibliothek-v0.1.pdf) und
[HTML-Fassung](konto-bibliothek-v0.1.html). Screenshots der lauffähigen Vue-Demo
mit synthetischen Daten; Vue und React teilen Controller und Darstellungskonzept.
[Einbindung und Demo starten](../account.md).

## Ursprünglicher Designentwurf

Stand: 29. September 2026. Statische Designvorlage mit synthetischen Daten.
Keine implementierte Anwendung; Kamera und E-Mail-Versand werden nicht aktiviert.

- [PDF öffnen](konto-mandant-gui.pdf): 13 Seiten im A4-Querformat.
- [HTML-Druckvorlage öffnen](konto-mandant-gui.html): eigenständige Datei ohne
  JavaScript, externe Ressourcen oder echte Zugangsdaten.
- [Fachlicher Standard](../konto-mandant-best-practice.md).
- [Frontend- und Adminkonzept](../konto-mandant-admin-design.md).

## Ansichten

| Seite | Ansicht |
|---|---|
| 1 | Mein Konto: Name, Foto und dienstliche Zuordnung |
| 2 | Kontakt und Passwortänderung, nebeneinander zur Erläuterung |
| 3 | Bild hochladen, zuschneiden, drehen und positionieren |
| 4 | Webcam aktivieren, Vorschau und Fotoaufnahme |
| 5 | Mandantenprofil mit Logo und Anschrift |
| 6 | Plattformweite Mandantenverwaltung |
| 7 | Mandant anlegen: erster Schritt des Assistenten |
| 8 | Plattformweite Nutzerverwaltung und Mitgliedschaften |
| 9 | Nutzer anlegen: Einladung, Startpasswort oder zentrale Anmeldung |
| 10 | Geschützte Rollenvorlage und Rechtematrix |
| 11 | Begrüßungstext bearbeiten und Einladungsvorschau |
| 12 | Einladungsnachricht und Begrüßung nach dem ersten Einstieg |
| 13 | Mobile Ansicht und Dunkelmodus |

Die Darstellung ist für Vue und React gemeinsam vorgesehen. Das PDF zeigt
ausgewählte Zustände und Hauptabläufe, keine vollständige Folge aller Dialoge.
Personenbilder und Kameravorschau verwenden bewusst schematische Platzhalter.
Das Logo wird über dieselbe Bildverarbeitung gepflegt, aber standardmäßig
vollständig eingepasst statt wie ein Personenfoto beschnitten.

## Erneut als PDF ausgeben

Die HTML-Datei in Chrome/Chromium öffnen und als PDF drucken: A4 quer,
Skalierung 100 Prozent, keine zusätzlichen Ränder oder Browser-Kopf-/Fußzeilen,
Hintergrundgrafiken einschalten. Das Stylesheet enthält feste Druckseiten.
Lato ist die lokal verwendete Schrift; bei fehlender Schrift können Umbrüche abweichen.

Die vorliegende PDF wurde mit Headless Chrome über Playwright erzeugt
(`preferCSSPageSize: true`, `printBackground: true`). Geprüft wurden Seitenzahl,
PDF-Text, Seitenformat, Überläufe der Hauptbereiche und gerasterte Seitenansichten.
Die Seiten wurden als Kontaktbogen sowie ausgewählte Ansichten vergrößert betrachtet.

Es wurden nur Dokumentationsartefakte erzeugt. Keine funktionale Kamera-,
Backend-, Vue-/React- oder Barrierefreiheitsabnahme und kein `auditcore-runner`-Lauf.
