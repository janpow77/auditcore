# Gemeinsame Seitenlayouts: Bestandsaufnahme und Übernahme

## Ziel

`@auditcore/layout` bündelt die wiederkehrenden Seitenbausteine. Die Fachseiten,
Authentifizierung, Mandantenrechte und tatsächlichen Datei-Exporte verbleiben
in den jeweiligen Anwendungen.

## Bestandsaufnahme der Repositories

| Repository | Vorhandene Oberfläche | Konsequenz für die Übernahme |
|---|---|---|
| `audit_designer` | Vue 3; `LoginView.vue` enthält bereits Fisch-/Wasseranimation; `AppHeader.vue` verwaltet Navigation, Profilmenüs und den Theme-Store; Exporte laufen über unterschiedliche Services. | Vue-Komponenten direkt einsetzen. Anmeldung und Kopfleiste schrittweise einbetten. Vorher bestehende Menüs/Guards als Slots übernehmen; `target="class"`, `storageKey="theme"`. `/auditlogo.png` für die Login-Fischanimation wiederverwenden. Exporte bleiben bei den jeweiligen Services. |
| `Rechnungslegung` | Vue; `AppKopf.vue` enthält Logo, mandantenabhängige Marke, mobile Menüs, Seminar-Modi und geladenes Profilbild; `App.vue` verwendet Vue-`Transition` für Routen. | `FaAppLayout` als strukturelle Hülle und Slots verwenden. Mandanten-, Rollen- und Seminarlogik in `AppKopf.vue` lassen. Für Profilbilder weiter die authentifizierte Blob-URL übergeben. |
| `DSGVO` | Vue-SPA mit Teilnehmer- und Verwaltungsansichten. | Vue-Komponenten können direkt eingebunden werden; Login- und Shell-Routen anhand der vorhandenen Ansichtsgrenzen trennen. |
| `schulungsframework` | Vue; vorhandener `ThemeToggle.vue` und `data-theme`; `@auditcore/ui` liegt als lokaler 0.3.0-Tarball bei. | Vue-Komponenten oder Web Components. `target="data-theme"`, `storageKey="seminar-theme"`; bestehende Theme-Variablen beibehalten. Paketversionen und Tarballs zusammen aktualisieren. |
| `flow-agent` | Vue; eigener Theme-Schalter, `data-theme`, reduzierte Bewegung und WAAPI-basierter Routenübergang. | `target="data-theme"`, `storageKey="flow-agent-theme"`. Den bisherigen WAAPI-Übergang bei Seiten mit `sticky`/`fixed` zunächst beibehalten oder gezielt gegen `FaPageTransition` prüfen. |
| `simex` | Vue/Pinia; Erscheinungszustand `dark`/`light`/`system` mit Storage-, Betriebssystem- und Tab-Synchronisierung. | `FaThemeSwitch` passt für den manuellen Wechsel, bildet aber den vollständigen Pinia-Zustand mit synchronisierten Tabs noch nicht ab. Entweder `FaThemeSwitch` erweitern oder die bestehende Appearance-Store-Logik als führenden Zustand behalten. |
| `regulierung` | React; `Login.tsx` hat eine animierte Fischillustration; `ThemeContext` speichert `hpp-theme`, `.dark` und `data-fa-theme`. | Über `@auditcore/layout/elements` als Light-DOM-Web Components einsetzbar; `target="class"`, `storageKey="hpp-theme"`. React-Context bleibt zuständig für App-Zustand. |
| `VideoArchivAssistent` | Flask/Jinja-Templates und servergerenderte Seiten; gemeinsame HTML-Vorlage und CSS. | Web Components lassen sich nach Bereitstellung der gebauten JS- und CSS-Dateien über Module-Script laden. Den Server-Login und Sessionablauf unverändert in Jinja belassen. |

## Einbettungswege

- **Vue-Anwendungen:** Vue-Komponenten aus `@auditcore/layout`; Router,
  Authentifizierung, Nutzerbild-URL und Exportfunktion bleiben bei der App.
- **React oder HTML:** `defineFlowauditLayoutElements()` registriert Custom
  Elements im Light DOM. Die Web Components benötigen Vue als Laufzeit-Peer;
  importierte Styles werden mit den App-Styles gebündelt.
- **Servergerenderte HTML-Seiten:** veröffentlichte Dateien aus dem Paket als
  Modulscript und Styles einbinden. Formular-POSTs, CSRF-Schutz und Session-Cookies
  verbleiben serverseitig.

## Integrationsreihenfolge

1. Im audit_designer eine geschützte Beispielroute mit `FaAppLayout`, Logo,
   Account-Bild, Theme-Schalter und `FaPageTransition` aufsetzen.
2. Login-Darstellung über `FaLoginLayout` austauschen und vorhandene
   Anmeldelogik, Fehlerzustände, TOTP-Eingabe und `/auditlogo.png` als
   `fishImage`/`logo` einstecken.
3. Exporte nur dort mit `FaExportActions` ersetzen, wo Speichern, PDF und JPG
   bereits über klar getrennte App-Handler verfügen.
4. Nach erfolgreichem Vue-Einsatz das Paket in den anderen Vue-Apps aktualisieren;
   React und Flask folgen über den Web-Component-Einstieg.

Diese Reihenfolge begrenzt das Risiko, dass Layout-Komponenten versehentlich
Anmelde-, Berechtigungs-, Datenlade- oder Dateiexportverträge verändern.
