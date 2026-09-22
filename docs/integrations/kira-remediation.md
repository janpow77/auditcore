# KIRA: unbestätigte Schreibzugriffe sicher wiederaufnehmen

## Ursache und Abhilfe

Der erste Detailimport wurde nach wiederholten Zeitüberschreitungen abgebrochen.
Ein Timeout bedeutet jedoch nicht, dass KIRA den Eintrag verworfen hat. Bisher
blieben nur erfolgreiche Bestätigungen persistent; ein erneuter Import konnte
denselben unbestätigten POST wiederholen. Zusätzlich gab KIRA bei einigen
Policy-/Quality-Dokumenten einen abweichenden, offenbar deduplizierten Inhalt
zurück. Diese Rückgaben wurden zu Recht nicht als Speicherung bestätigt.

Der Adapter journalisiert jetzt jeden Schreibversuch **vor** dem Request in einer
privaten, atomar ersetzten Datei `<ledger>.pending.json`. Eine fehlende Bestätigung,
ein Prozessabbruch, Timeout oder eine abweichende Rückgabe bleibt nach Neustarts
sichtbar. `sync()` stellt die betroffene Identität mit `REVIEW_REQUIRED` und
`deferred` zurück, auch wenn sich zwischenzeitlich der lokale Inhalt geändert hat.
Bestätigungsjournale werden ausschließlich nach einer passenden Rückgabe aktualisiert.

`KiraKnowledgeStore.reconcile()` verwendet den vorhandenen paginierten
`GET /entries`-Vertrag. Ein Eintrag gilt erst dann als bestätigt, wenn die gesamte
abgefragte Liste vollständig ist, genau eine passende `source_ref` vorkommt und
die Dokumentbytes übereinstimmen. Uneindeutige Identitäten, Seitenlimits,
Transportfehler oder abweichende Inhalte bleiben `REVIEW_REQUIRED`.
Semantische Suche wird nicht zum Nachweis einer Dokumentidentität verwendet.

Eine begrenzte Wiederabstimmung lässt sich mit der vorhandenen lokalen
graphify-kira-Konfiguration ausführen:

```bash
python scripts/sync_kira_reconcile.py OWNER/REPOSITORY --max-pages 3 \
  --output .auditcore/kira-reconciliation.json
```

Das Skript sendet ausschließlich GET-Requests. Es kann Bestätigungsjournale lokal
ergänzen; es erzeugt, ändert oder löscht keine entfernten Dokumente. Die historischen
Sammelberichte werden nicht überschrieben. Für die alte, vor Einführung des Journals
abgebrochene Inventur ist zuerst diese Wiederabstimmung nötig, bevor Detailimporte
erneut gestartet werden. Fehlende alte Dokumente werden dabei ausdrücklich
zurückgestellt; ein fehlender Such-/Listentreffer ist keine Schreibfreigabe.

## Tatsächlich ausgeführter Nachweis

Für `janpow77/flowlib` wurde eine vollständige Liste gelesen und alle drei lokalen
Inventardokumente anhand ihrer Identität und ihres exakten Inhalts bestätigt.
Der zuvor mit `TimeoutError` gemeldete Eintrag
`auditcore:163bff5004d6862dd8cb1ee1c072a88ec92140dda1b0673e6ac5262a9e3a2110`
war bereits serverseitig gespeichert. Seine bisher fehlende Bestätigung wurde
ohne Wiederholung des POSTs ergänzt. Die beiden anderen Bestätigungen wurden
erneut gelesen. Remote-Schreibzugriffe bei dieser Wiederabstimmung: **0**.

Privater Laufnachweis: `.auditcore/kira-reconciliation-flowlib.json`.
Dies bestätigt nur die dort inventarisierte GitHub-Revision, weder einen neueren
Codezustand noch die Vollständigkeit des gesamten KIRA-Imports.

## Verbleibende externe und operative Punkte

- Die anderen unterbrochenen Repository-Importe müssen ebenfalls zunächst
  lesend abgeglichen werden. Der globale Detailimport bleibt `PARTIAL`.
- Die vier abweichenden Policy-/Quality-Rückgaben werden nicht erneut geschrieben.
  Der KIRA-Betreiber muss getrennte, stabile `source_ref`-Identitäten erhalten
  und darf ähnliche Dokumente verschiedener Identitäten nicht automatisch
  zusammenführen. Danach sind exakte Rücklesetests und gegebenenfalls eine
  kontrollierte Reparatur der betroffenen Einträge nötig.
- Inhaltsfilterablehnungen bleiben erhalten. Es werden keine Begriffe verändert,
  versteckt oder entfernt, um den Filter zu umgehen. Benötigt wird eine fachliche
  Prüfung der Filterentscheidung bzw. eine zulässige Indexierungsentscheidung.
- Das clientseitige Journal ersetzt keinen serverseitigen Idempotenzschlüssel.
  Langfristig sollte der API-Vertrag atomare Upserts je `source_ref` sowie eine
  direkte Abfrage dieser Identität anbieten. Gleichzeitige Prozesse dürfen
  nicht dieselbe lokale Ledger-Datei beschreiben.

Gezielte Regressionstests decken Timeout mit tatsächlicher Speicherung,
Prozessneustart, geänderte Inhalte bei ungeklärter Identität, verlorene
Update-Bestätigung, vollständige Pagination, Inhalts-/Identitätsabweichungen,
Duplikate und Seitenlimits ab. Credentials und rohe Fehlertexte werden nicht
in das Journal übernommen.
