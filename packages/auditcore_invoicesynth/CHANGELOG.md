# Changelog auditcore_invoicesynth

Rekonstruiert aus der Git-Historie (Pull Requests #46, #48, #79).

## 0.1.0 – 2026-09-24

- Neues Paket (Entscheidung E1): Anreicherung der Datensätze aus
  `auditcore_invoicegenerator` mit prüfziffer-gültigen fiktiven IBAN/BIC und
  USt-IdNr./UID (E5), Steuerschemata DE/AT, zehn Vorlagen (zwei nur im
  Layout-Holdout), Beschriftungs-Synonyme, deutsche Zahlen- und Datumsformate,
  freie Systemschriften mit SHA-256 im Manifest (nicht eingebettet),
  seed-bestimmtes Scanrauschen, Donut-Ausgabe (`metadata.jsonl`, Manifest,
  Datensatz-Hash), Ziel-JSON `auditcore_invoice_v1` nur mit Kopf- und
  Summenfeldern (E8) und Bewertung mit den Abnahmeschwellen aus E6 (#46).
- Beschriftung und Wert überlappen in Kopfspalte und Summenblock nicht mehr
  (Sichtprüfung des Piloten, #46).
- Donut-Nachtraining vorbereitet, ohne echtes Training (Etappe E3):
  `auditcore_invoicesynth.train` mit Profilen, Rechenortwahl,
  Checkpoints und Wiederaufnahme, Extra `[train]` (#48).
- 2026-09-25: Abhängigkeit auf `auditcore_invoicegenerator==0.2.1` angehoben
  (#79), ohne Versionsänderung dieses Pakets.
