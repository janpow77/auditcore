# Versionierte Rechnungsprofile

Die Profile `flowinvoice-demo-fb2d185` und `invoice-scenario-v1` sind getrennte
fachliche Artefakte. Ihre stabilen IDs, Typen, Titel, Versionen, Zeitbezüge,
Quellbezüge und Inhaltshashes stehen in der mitinstallierten `provenance.json`.
Der Erstellungszeitpunkt bezeichnet die tatsächlich beobachtete lokale
Characterization/Extraktion, nicht die unbekannte ursprüngliche Erstellung.
Unbelegte Autoren, Eigentümer und Organisationen bleiben `UNKNOWN`.

Die namespaced Artefakt-ID identifiziert den Profileintrag. Das separate Feld
`runtime_profile_id` bindet ihn an den tatsächlichen Laufzeitbezug: beim neuen
Szenario `InvoiceRecord.metadata.profile == synthetic-scenario-v1`, beim Legacy-
Profil die öffentliche Konstante `FLOWINVOICE_DEMO_PROFILE`. Der historische
Legacy-Rechnungsdatensatz erhält dadurch keine zusätzlichen Felder. Ein
ausgeführter Test prüft beide Zuordnungen gegen die installierte Bibliothek.

Beide Artefakte sind `DRAFT`. Es gibt noch keine zuvor veröffentlichte
Paketversion; `predecessor_version: null` bedeutet genau das. Das Legacyprofil
referenziert unabhängig davon den konkreten historischen Quellcommit als
Fork-Ursprung. Das Szenarioprofil besitzt keinen gleichgesetzten Legacyvertrag.

Bei fachlichen Änderungen wird ein nachvollziehbarer Entwurf mit geänderten
Inhaltshashes, Änderungsbegründung und Regressionsergebnissen erstellt. Vor einer
Veröffentlichung werden Vorgängerversion, Quell-Diff, betroffene Goldenergebnisse
und fachliche Vertragsänderungen gemeinsam geprüft. Für das Legacyprofil sind
vollständige Rechnungen, Fehlerlabels und RNG-Ziehfolgen die Diff-Grundlage;
abweichende Ergebnisse verlangen eine ausdrückliche Entscheidung oder ein neu
benanntes Profil. Golden-Daten werden nicht zur bloßen Fehlerbeseitigung ersetzt.

Technischer Code-Review, beobachtete Tests und Rechtefreigabe sind getrennte
Nachweise. Ein technischer Review durch Agenten ersetzt keine erforderliche
Freigabe des Rechteinhabers. Reviewer und Entscheidungen werden erst nach der
tatsächlichen Prüfung im Release-Nachweis eingetragen. Es wird keine menschliche
Freigabe aus einer erfolgreichen Testausführung abgeleitet.

Freigegebene oder veröffentlichte Versionen dürfen nicht überschrieben werden.
Neue fachliche Inhalte erhalten eine neue Version mit Vorgängerbezug; vorhandene
Wheels, SDists und Digests bleiben erhalten. Der Paketquellenbetreiber muss das
Überschreiben einer bestehenden veröffentlichten Version verhindern. Rollback
installiert ein identifiziertes älteres Artefakt, ohne dessen Historie zu ändern.
Die Bibliothek selbst ist kein Versionsserver und behauptet keinen bereits
konfigurierten öffentlichen Release-Schutz. Die Lizenzentscheidung ist seit der
ausdrücklichen Nutzerfreigabe am 22.09.2026 `USER_AUTHORIZED_MIT`; technische
Releaseprüfung und tatsächliche Publikation sind davon getrennt. Bis deren
Abschluss bleibt der Artefaktstatus `DRAFT`.

Die Tests prüfen installierte Profil-Inhalte gegen ihre Hashreferenzen, die
unveränderten beobachteten Legacyausgaben und den dokumentierten Fork-Ursprung.
Die Profile enthalten keine Prompts oder Agenten: Die speziellen Prompt-/Agent-
Prüfungen T-26 bis T-29 sind dafür nicht anwendbar.
